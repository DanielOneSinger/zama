import asyncio
import logging
import time
import yaml
import eth_account
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LighterInitializer:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
    
    async def initialize_api_key(self):
        """初始化Lighter API密钥"""
        lighter_config = self.config['exchanges']['lighter']
        base_url = lighter_config['base_url']
        wallet_private_key = lighter_config['wallet_private_key']
        account_index = lighter_config['account_index']
        api_key_index = lighter_config['api_key_index']
        
        if not wallet_private_key:
            logger.error("钱包私钥未配置，请在config.yaml中设置wallet_private_key")
            return False
        
        try:
            # 导入lighter模块
            import lighter
            
            # 验证账户是否存在并获取账户索引
            try:
                api_client = lighter.ApiClient(configuration=lighter.Configuration(host=base_url))
                eth_acc = eth_account.Account.from_key(wallet_private_key)
                eth_address = eth_acc.address
                
                logger.info(f"正在验证账户: {eth_address}")
                
                response = await lighter.AccountApi(api_client).accounts_by_l1_address(l1_address=eth_address)
                
                if len(response.sub_accounts) > 1:
                    logger.warning(f"发现多个账户索引: {len(response.sub_accounts)}")
                    for sub_account in response.sub_accounts:
                        logger.info(f"账户索引: {sub_account.index}")
                
                # 使用配置中的account_index或第一个找到的
                if account_index is None:
                    account_index = response.sub_accounts[0].index
                    self.config['exchanges']['lighter']['account_index'] = account_index
                
                logger.info(f"使用账户索引: {account_index}")
                
            except Exception as e:
                error_msg = str(e)
                if "account not found" in error_msg.lower():
                    logger.error(f"账户未找到: {eth_address}")
                    return False
                else:
                    logger.error(f"验证账户失败: {e}")
                    return False
            
            # 创建新的API密钥对
            logger.info("正在生成新的API密钥...")
            try:
                result = lighter.create_api_key()
                if len(result) != 3:
                    logger.error("生成API密钥失败: 返回值格式错误")
                    return False
                    
                private_key, public_key, err = result
                if err is not None:
                    logger.error(f"生成API密钥失败: {err}")
                    return False
            except Exception as e:
                logger.error(f"生成API密钥失败: {e}")
                return False
            
            # 创建交易客户端
            try:
                tx_client = lighter.SignerClient(
                    url=base_url,
                    private_key=private_key,
                    account_index=account_index,
                    api_key_index=api_key_index,
                )
            except Exception as e:
                logger.error(f"创建交易客户端失败: {e}")
                return False
            
            # 更改API密钥
            logger.info("正在更新API密钥...")
            try:
                result = await tx_client.change_api_key(
                    eth_private_key=wallet_private_key,
                    new_pubkey=str(public_key),  # 确保是字符串类型
                )
                if len(result) != 2:
                    logger.error("更新API密钥失败: 返回值格式错误")
                    return False
                    
                response, err = result
                if err is not None:
                    logger.error(f"更新API密钥失败: {err}")
                    return False
            except Exception as e:
                logger.error(f"更新API密钥失败: {e}")
                return False
            
            # 等待服务器更新
            logger.info("等待服务器更新API密钥...")
            time.sleep(10)
            
            # 验证客户端
            try:
                err = tx_client.check_client()
                if err is not None:
                    logger.error(f"验证客户端失败: {err}")
                    return False
            except Exception as e:
                logger.error(f"验证客户端失败: {e}")
                return False
            
            # 更新配置文件
            self.config['exchanges']['lighter']['api_key_private_key'] = private_key
            self.save_config()
            
            logger.info("API密钥初始化成功!")
            logger.info(f"新的API私钥已保存到配置文件: {private_key[:20]}...")
            
            try:
                await tx_client.close()
                await api_client.close()
            except:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"初始化过程中发生错误: {e}")
            return False


async def main():
    """主函数"""
    initializer = LighterInitializer()
    success = await initializer.initialize_api_key()
    
    if success:
        print("\n✅ Lighter API密钥初始化成功!")
        print("现在可以运行套利机器人了。")
    else:
        print("\n❌ Lighter API密钥初始化失败!")
        print("请检查配置文件和网络连接。")


if __name__ == "__main__":
    asyncio.run(main()) 