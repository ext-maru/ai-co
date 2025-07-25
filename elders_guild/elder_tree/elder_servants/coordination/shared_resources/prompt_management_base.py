from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from litellm.types.llms.openai import AllMessageValues
from litellm.types.utils import StandardCallbackDynamicParams

class PromptManagementClient(TypedDict):
    prompt_id: str

    completed_messages: Optional[List[AllMessageValues]]

class PromptManagementBase(ABC):
    @property
    @abstractmethod
    def integration_name(self) -> str:
        pass

    @abstractmethod
    def should_run_prompt_management(:
        self,
        prompt_id: str,
        dynamic_callback_params: StandardCallbackDynamicParams,
    ) -> bool:
        pass

    @abstractmethod
    def _compile_prompt_helper(:
        self,
        prompt_id: str,
        prompt_variables: Optional[dict],
        dynamic_callback_params: StandardCallbackDynamicParams,
        prompt_label: Optional[str] = None,
    ) -> PromptManagementClient:
        pass

    def merge_messages(:
        self,

        client_messages: List[AllMessageValues],
    ) -> List[AllMessageValues]:

    def compile_prompt(:
        self,
        prompt_id: str,
        prompt_variables: Optional[dict],
        client_messages: List[AllMessageValues],
        dynamic_callback_params: StandardCallbackDynamicParams,
        prompt_label: Optional[str] = None,
    ) -> PromptManagementClient:
        compiled_prompt_client = self._compile_prompt_helper(
            prompt_id=prompt_id,
            prompt_variables=prompt_variables,
            dynamic_callback_params=dynamic_callback_params,
            prompt_label=prompt_label,
        )

        try:

        except Exception as e:
            raise ValueError(
                f"Error compiling prompt: {e}. Prompt id={prompt_id}, prompt_variables={prompt_variables}, client_messages={client_messages}, dynamic_callback_params={dynamic_callback_params}"
            )

        compiled_prompt_client["completed_messages"] = messages
        return compiled_prompt_client

    def _get_model_from_prompt(:
        self, prompt_management_client: PromptManagementClient, model: str
    ) -> str:

        else:
            return model.replace("{}/".format(self.integration_name), "")

    def get_chat_completion_prompt(:
        self,
        model: str,
        messages: List[AllMessageValues],
        non_default_params: dict,
        prompt_id: Optional[str],
        prompt_variables: Optional[dict],
        dynamic_callback_params: StandardCallbackDynamicParams,
        prompt_label: Optional[str] = None,
    ) -> Tuple[str, List[AllMessageValues], dict]:
        if prompt_id is None:
            raise ValueError("prompt_id is required for Prompt Management Base class")
        if not self.should_run_prompt_management(:
            prompt_id=prompt_id, dynamic_callback_params=dynamic_callback_params
        ):
            return model, messages, non_default_params

            prompt_id=prompt_id,
            prompt_variables=prompt_variables,
            client_messages=messages,
            dynamic_callback_params=dynamic_callback_params,
            prompt_label=prompt_label,
        )

        )

        updated_non_default_params = {
            **non_default_params,

        }

        model = self._get_model_from_prompt(

        )

        return model, completed_messages, updated_non_default_params
