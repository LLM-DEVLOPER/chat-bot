from typing import Dict, Optional, Callable, Union, Type

from core.exceptions import ModuleInitializationError
from modules.base_handler import BaseHandler
from modules.base_module import BaseModule
from utils.logging_setup import logger


async def initialize_single_module_instance(
        module_id: str,
        module_config: dict,
        factory_dict: Dict[str, Callable[..., Union[BaseModule, BaseHandler]]],
        base_class: Union[Type[BaseModule], Type[BaseHandler]],
        existing_modules: Dict[str, Union[BaseModule, BaseHandler]],
) -> Optional[Union[BaseModule, BaseHandler]]:
    """
    通用函数，用于初始化单个模块实例。
    处理配置检查、工厂查找、实例创建、类型验证和错误捕获。

    Args:
        module_id (str): 模块的唯一标识符。
        module_config (dict): 当前模块的配置。
        factory_dict (Dict[str, Callable]): 模块工厂函数的字典，用于创建模块实例。
        base_class (Union[Type[BaseModule], Type[BaseHandler]]): 模块实例应继承的基类，用于类型检查。
        existing_modules (Dict[str, Union[BaseModule, BaseHandler]]): 已加载模块的字典，用于检查重复。

    Returns:
        Optional[Union[BaseModule, BaseHandler]]: 初始化成功的模块实例，失败则返回 None。
    """
    if not isinstance(module_config, dict):
        logger.error("模块 '%s' 的配置必须是 dict，实际为: %s", module_id, type(module_config).__name__)
        return None

    if module_id in existing_modules:
        logger.warning("模块 '%s' 已存在，跳过初始化。", module_id)
        return None

    factory = factory_dict.get(module_id)
    if not factory:
        logger.error("未注册模块类型 '%s' 的创建工厂函数。", module_id)
        return None

    try:
        logger.info("初始化模块 '%s'...", module_id)
        # 调用工厂函数创建模块实例
        module_instance: Union[BaseModule, BaseHandler] = factory(
            module_id=module_id,
            config=module_config
        )

        # 验证模块实例的类型
        if not isinstance(module_instance, base_class):
            raise ModuleInitializationError(
                f"模块 '{module_id}' 实例不是 {base_class.__name__} 的子类，实际类型: {type(module_instance).__name__}"
            )

        # 初始化模块并添加到已加载模块字典
        await module_instance.initialize()
        existing_modules[module_id] = module_instance  # 在这里直接修改传入的字典
        logger.info("模块 '%s' 初始化成功。", module_id)
        return module_instance

    except ModuleInitializationError as e:
        logger.error("模块 '%s' 初始化失败: %s", module_id, e)
    except Exception as e:
        logger.exception("模块 '%s' 初始化时发生异常: %s", module_id, e)
    return None
