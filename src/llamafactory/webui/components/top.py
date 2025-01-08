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
   <div id="web3auth-container" style="text-align: right;">
       <div id="login-container">
            <img class="logo-image" src="https://i.ibb.co/drdFdGT/opl-logo.png" alt="openledger-logo">
            <div>
            <i class="fa fa-industry" style="font-size:28px;"></i>
            <span class="logo-text">Model Factory</span>
            </div>
           <button id="web3auth-login" class="lg primary">Connect Wallet</button>
           <div id="user-info" style="display:none;">
           <div class="user-profile">
               <img id="user-image" class="profile-image" src="" alt="Profile">
               <div class="dropdown">
                   <button class="dropbtn" id="user-name"></button>
                   <div class="dropdown-content">
                       <a href="#" style="color: white;" id="profile-link">Profile</a>
                       <a href="#" style="color: white;" id="web3auth-logout">Logout</a>
                   </div>
               </div>
           </div>
       </div>
       </div>
       
   </div>
   '''

if is_gradio_available():
    import gradio as gr


if TYPE_CHECKING:
    from gradio.components import Component


def create_top() -> Dict[str, "Component"]:
    available_models = list(SUPPORTED_MODELS.keys()) + ["Custom"]

    with gr.Blocks() as ui:
        ui.css = """
        .logo-image {
            margin-left: 0;
            background-color: Transparent !important;
        }
        """

        with gr.Row():
            # gr.Image("Layer-open.png", elem_classes="logo-image", scale=0.1, show_label=False, show_download_button=False, show_fullscreen_button=False)
            gr.HTML(value=only_html)
    # with gr.Blocks():
    #     gr.HTML(value=only_html)

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
