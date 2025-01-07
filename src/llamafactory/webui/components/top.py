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

from typing import TYPE_CHECKING, Dict

from ...data import TEMPLATES
from ...extras.constants import METHODS, SUPPORTED_MODELS
from ...extras.packages import is_gradio_available
from ..common import get_model_info, list_checkpoints, save_config
from ..utils import can_quantize, can_quantize_to


only_html = '''
<h1>Gradio with Web3Auth</h1>
    

    <div id="app">
        <button id="login" onclick="login">Login</button>
        <div id="userData" style="display:none;">
            <p id="address"></p>
            <button id="logout">Logout</button>
        </div>
    </div>
'''

header='''
    <title>Gradio with Web3Auth</title>
    <script src="https://cdn.jsdelivr.net/npm/@web3auth/modal@9.5.1/dist/modal.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@web3auth/ethereum-provider@9.5.1/dist/ethereumProvider.umd.min.js"></script>
    <script type="text/javascript">
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

window.onload = function() {
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
  // Avoid using public rpcTarget in production.
  // Use services like Infura, Quicknode etc
  
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
    
    
    setTimeout(function(){
        console.log('id inside settimeout :', document.getElementById('login'))
        document.getElementById('login').onclick = login;
        document.getElementById('logout').onclick = logout;
    }, 3000)
    console.log(document.getElementById('login'))
   async function login() {
    try {
        console.log("inside login")
        await web3auth.initModal();
        const provider = await web3auth.connect();
        console.log("ethereumProvider", ethereumProvider)
        // await ethereumProvider.init();
        const address = await ethereumProvider.request({ method: "eth_accounts" });
        
        document.getElementById('address').textContent = 'Connected: ' + address[0];
        document.getElementById('userData').style.display = 'block';
        document.getElementById('login').style.display = 'none';
        console.log(window.parent.location)
        window.top.postMessage({ action: 'sendData', data: 'Hello from iframe!' }, '*');
        console.log("address", address);
        return address;
    } catch (error) {
        console.error(error);
    }
}
    
    async function logout() {
        await web3auth.logout();
        document.getElementById('userData').style.display = 'none';
        document.getElementById('login').style.display = 'block';
    }
    console.log('id is :', document.getElementById('login'))
    }
</script>
    
'''



if is_gradio_available():
    import gradio as gr


if TYPE_CHECKING:
    from gradio.components import Component


def create_top() -> Dict[str, "Component"]:
    available_models = list(SUPPORTED_MODELS.keys()) + ["Custom"]
    
    with gr.Blocks(head=header) as demo:
        gr.HTML(value=only_html)
        action_button = gr.Button(value="Name", elem_id="my_btn")
        textbox = gr.Textbox()
        action_button.click(lambda : "button pressed", None, textbox)


    with gr.Row():
        lang = gr.Dropdown(choices=["en", "ru", "zh", "ko"], scale=1)
        model_name = gr.Dropdown(choices=available_models, scale=3)
        model_path = gr.Textbox(scale=3)

    with gr.Row():
        finetuning_type = gr.Dropdown(choices=METHODS, value="lora", scale=1)
        checkpoint_path = gr.Dropdown(multiselect=True, allow_custom_value=True, scale=6)

    with gr.Row():
        quantization_bit = gr.Dropdown(choices=["none", "8", "4"], value="none", allow_custom_value=True, scale=2)
        quantization_method = gr.Dropdown(choices=["bitsandbytes", "hqq", "eetq"], value="bitsandbytes", scale=2)
        template = gr.Dropdown(choices=list(TEMPLATES.keys()), value="default", scale=2)
        rope_scaling = gr.Radio(choices=["none", "linear", "dynamic"], value="none", scale=3)
        booster = gr.Radio(choices=["auto", "flashattn2", "unsloth", "liger_kernel"], value="auto", scale=5)

    model_name.change(get_model_info, [model_name], [model_path, template], queue=False).then(
        list_checkpoints, [model_name, finetuning_type], [checkpoint_path], queue=False
    )
    model_name.input(save_config, inputs=[lang, model_name], queue=False)
    model_path.input(save_config, inputs=[lang, model_name, model_path], queue=False)
    finetuning_type.change(can_quantize, [finetuning_type], [quantization_bit], queue=False).then(
        list_checkpoints, [model_name, finetuning_type], [checkpoint_path], queue=False
    )
    checkpoint_path.focus(list_checkpoints, [model_name, finetuning_type], [checkpoint_path], queue=False)
    quantization_method.change(can_quantize_to, [quantization_method], [quantization_bit], queue=False)

    return dict(
        lang=lang,
        model_name=model_name,
        model_path=model_path,
        finetuning_type=finetuning_type,
        checkpoint_path=checkpoint_path,
        quantization_bit=quantization_bit,
        quantization_method=quantization_method,
        template=template,
        rope_scaling=rope_scaling,
        booster=booster,
    )
