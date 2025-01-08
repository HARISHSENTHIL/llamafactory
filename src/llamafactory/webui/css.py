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

CSS = r"""
.duplicate-button {
  margin: auto !important;
  color: white !important;
  background: black !important;
  border-radius: 100vh !important;
}

.modal-box {
  position: fixed !important;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%); /* center horizontally */
  max-width: 1000px;
  max-height: 750px;
  overflow-y: auto;
  background-color: var(--input-background-fill);
  flex-wrap: nowrap !important;
  border: 2px solid black !important;
  z-index: 1000;
  padding: 10px;
}

.dark .modal-box {
  border: 2px solid white !important;
}
.user-profile {
    display: flex;
    align-items: center;
    justify-content: end;
    gap: 10px;
}

.profile-image {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
}

.dropdown {
    position: relative;
    display: inline-block;
}

.dropbtn {
    background-color: transparent;
    border: none;
    cursor: pointer;
    padding: 8px;
}

.dropdown-content {
    display: none;
    position: absolute;
    color: white;
    background-color: #1f2937;
    min-width: 160px;
    box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
    z-index: 1;
    right: 0;
}

.dropdown-content a {
    color: black;
    padding: 12px 16px;
    text-decoration: none;
    display: block;
}

.dropdown-content a:hover {
    background-color: transparent;
}

.dropdown:hover .dropdown-content {
    display: block;
}

#login-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
}


#web3auth-login {
    border-radius: var(--button-large-radius);
    padding: var(--button-large-padding);
    font-weight: var(--button-large-text-weight);
    font-size: var(--button-large-text-size);
    border: var(--button-border-width) solid var(--button-primary-border-color);
    background: var(--button-primary-background-fill);
    color: var(--button-primary-text-color);
}
.logo-text {
    font-size: 30px;
    margin-left: 10px;
}
"""
