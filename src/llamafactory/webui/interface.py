# Copyright 2024 the LlamaFactory team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import platform
import time

from ..extras.packages import is_gradio_available
from .common import save_config
from .components import (
    create_chat_box,
    create_eval_tab,
    create_export_tab,
    create_infer_tab,
    create_top,
    create_train_tab,
)
from .css import CSS
from .engine import Engine

if is_gradio_available():
    import gradio as gr

header='''
    <title>Gradio with Web3Auth</title>
    <script src="https://cdn.jsdelivr.net/npm/@web3auth/modal@9.5.1/dist/modal.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@web3auth/ethereum-provider@9.5.1/dist/ethereumProvider.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <script type="text/javascript">

    setTimeout(function() {
    let btn = document.getElementById('tg-button');
    if(btn) {
        btn.click();
    }
    }, 2000)
    

function shortcuts(e) {
    console.log('key pressed')
    var event = document.all ? window.event : e;
    switch (e.target.tagName.toLowerCase()) {
        case "input":
        case "textarea":
        break;
        default:
        if (e.key.toLowerCase() == "s" && e.shiftKey) {
            document.getElementById("my_btn").click();
        }
    }
}
document.addEventListener('keypress', shortcuts, false);
setTimeout(function() {
function check() {
console.log("data")
}
const chainConfig = {
  chainNamespace: 'eip155',
  chainId: "0xaa36a7",
  rpcTarget: "https://rpc.ankr.com/eth_sepolia",
  displayName: "Ethereum Sepolia Testnet",
  blockExplorerUrl: "https://sepolia.etherscan.io",
  ticker: "ETH",
  tickerName: "Ethereum",
  decimals: 18,
  logo: "https://cryptologos.cc/logos/ethereum-eth-logo.png",
};

console.log("wind", window.EthereumProvider)
    const ethereumProvider = new window.EthereumProvider.EthereumPrivateKeyProvider({
        config: { chainConfig: {
            chainId: "0xaa36a7",
  rpcTarget: "https://rpc.ankr.com/eth_sepolia",
  chainNamespace: "eip155",
        } },
    });
    const web3auth = new window.Modal.Web3Auth({
        privateKeyProvider: ethereumProvider,
        web3AuthNetwork: "sapphire_devnet",
        clientId: "BD_mes2shHCQIycGpb1E6o8OWYzLOnjFBHgv9nYd3xHl5xE3XjG8qjaT5g1_jEVPWJ8ZTexeZiuXFwYb-9avE1Y", // Get from Web3Auth Dashboard
        chainConfig: {
            chainNamespace: "eip155",
            chainId: "0xaa36a7",
            rpcTarget: "https://rpc.ankr.com/eth_sepolia"
        }
    });
    console.log(document.getElementById('login'))
   async function login() {

        !web3auth.provider ? await web3auth.initModal() : console.log("Already provider initiated");
        const provider = await web3auth.connect();
        
        // Get user info from Web3Auth
        const userInfo = await web3auth.getUserInfo();
        console.log("User info:", userInfo);
        
        const address = await ethereumProvider.request({ method: "eth_accounts" });
        
        // Update UI with user info
        if (userInfo.profileImage) {
            document.getElementById('user-image').src = userInfo.profileImage;
        }
        if(document.querySelector('#wallet-address')) {
        let box = document.querySelector('#wallet-address-textbox label textarea');
            box.value = address[0];
            box.dispatchEvent(new Event('input'));
        }
        
        document.getElementById('user-name').textContent = userInfo.name || address[0].slice(0, 6) + '...';
        document.getElementById('wallet-address').textContent = address[0]
        document.getElementById('user-info').style.display = 'flex';
        document.getElementById('web3auth-login').style.display = 'none';
        
        window.top.postMessage({ action: 'sendData', data: 'Hello from iframe!' }, '*');
        return address;
}

async function logout() {
    await web3auth.logout();
    document.getElementById('user-info').style.display = 'none';
    document.getElementById('web3auth-login').style.display = 'block';
    document.getElementById('user-image').src = '';
    document.getElementById('user-name').textContent = '';
    if(document.querySelector('#wallet-address')) {
        let box = document.querySelector('#wallet-address-textbox label textarea');
            box.value = '';
            box.dispatchEvent(new Event('input'));
        }
}
    setTimeout(function(){
        console.log('id inside settimeout :', document.getElementById('login'))
        document.getElementById('web3auth-login').onclick = login;
        document.getElementById('web3auth-logout').onclick = logout;
    }, 3000)
    console.log('id is :', document.getElementById('login'))
    }, 2000);

</script>

'''


def create_ui(demo_mode: bool = False) -> "gr.Blocks":
    engine = Engine(demo_mode=demo_mode, pure_chat=False)
    hostname = os.getenv("HOSTNAME", os.getenv("COMPUTERNAME", platform.node())).split(".")[0]

    with gr.Blocks(title=f"LLaMA Board ({hostname})", css=CSS, head=header) as demo:
        if demo_mode:
            gr.HTML("<h1><center>LLaMA Board: A One-stop Web UI for Getting Started with LLaMA Factory</center></h1>")
            gr.HTML(
                '<h3><center>Visit <a href="https://github.com/hiyouga/LLaMA-Factory" target="_blank">'
                "LLaMA Factory</a> for details.</center></h3>"
            )
            gr.DuplicateButton(value="Duplicate Space for private use", elem_classes="duplicate-button")

        engine.manager.add_elems("top", create_top())
        lang: "gr.Dropdown" = engine.manager.get_elem_by_id("top.lang")

        with gr.Tab("Train"):
            engine.manager.add_elems("train", create_train_tab(engine))

        with gr.Tab("Evaluate & Predict"):
            engine.manager.add_elems("eval", create_eval_tab(engine))

        with gr.Tab("Chat"):
            engine.manager.add_elems("infer", create_infer_tab(engine))

        if not demo_mode:
            with gr.Tab("Export"):
                engine.manager.add_elems("export", create_export_tab(engine))

        demo.load(engine.resume, outputs=engine.manager.get_elem_list(), concurrency_limit=None)
        lang.change(engine.change_lang, [lang], engine.manager.get_elem_list(), queue=False)
        lang.input(save_config, inputs=[lang], queue=False)

    return demo


def create_web_demo() -> "gr.Blocks":
    engine = Engine(pure_chat=True)

    with gr.Blocks(title="Web Demo", css=CSS) as demo:
        lang = gr.Dropdown(choices=["en", "ru", "zh", "ko"], scale=1)
        engine.manager.add_elems("top", dict(lang=lang))

        _, _, chat_elems = create_chat_box(engine, visible=True)
        engine.manager.add_elems("infer", chat_elems)

        demo.load(engine.resume, outputs=engine.manager.get_elem_list(), concurrency_limit=None)
        lang.change(engine.change_lang, [lang], engine.manager.get_elem_list(), queue=False)
        lang.input(save_config, inputs=[lang], queue=False)

    return demo


def run_web_ui() -> None:
    gradio_ipv6 = os.getenv("GRADIO_IPV6", "0").lower() in ["true", "1"]
    gradio_share = os.getenv("GRADIO_SHARE", "0").lower() in ["true", "1"]
    server_name = os.getenv("GRADIO_SERVER_NAME", "[::]" if gradio_ipv6 else "0.0.0.0")
    create_ui().queue().launch(share=gradio_share, server_name=server_name, inbrowser=True)


def run_web_demo() -> None:
    gradio_ipv6 = os.getenv("GRADIO_IPV6", "0").lower() in ["true", "1"]
    gradio_share = os.getenv("GRADIO_SHARE", "0").lower() in ["true", "1"]
    server_name = os.getenv("GRADIO_SERVER_NAME", "[::]" if gradio_ipv6 else "0.0.0.0")
    create_web_demo().queue().launch(share=gradio_share, server_name=server_name, inbrowser=True)
