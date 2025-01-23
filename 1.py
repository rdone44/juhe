import dns.resolver
import os
from dotenv import load_dotenv
import time

def load_config():
    # 优先使用环境变量，如果没有则加载.env文件
    if not any([
        os.environ.get('API_URL_REGIONS'),
        os.environ.get('DOMAIN_SUFFIX'),
        os.environ.get('DNS_SERVER'),
        os.environ.get('DNS_TIMEOUT')
    ]):
        # 如果环境变量都不存在，则尝试加载.env文件
        load_dotenv()
        print("使用.env文件配置")
    else:
        print("使用环境变量配置")
    
    # 获取配置（优先使用环境变量）
    regions = os.getenv('API_URL_REGIONS')
    domain_suffix = os.getenv('DOMAIN_SUFFIX')
    dns_server = os.getenv('DNS_SERVER')
    timeout = os.getenv('DNS_TIMEOUT')
    
    # 验证必要的配置是否存在
    if not all([regions, domain_suffix, dns_server, timeout]):
        raise ValueError("缺少必要的配置参数，请检查环境变量或.env文件")
    
    # 处理地区代码列表
    regions = [r.strip() for r in regions.split(',') if r.strip()]
    
    # 生成域名列表
    domains = [f"{region}.{domain_suffix}" for region in regions]
    
    return {
        'domains': domains,
        'dns_server': dns_server,
        'timeout': int(timeout)
    }

def get_all_domain_ips(domain, resolver, max_retries=5):
    # 从域名中提取地区代码
    region = domain.split('.')[0]
    result = []
    
    # DNS服务器列表（按优先级排序）
    dns_servers = [
        '114.114.114.114',  # 国内DNS，通常较快
        '223.5.5.5',        # 阿里DNS
        '119.29.29.29',     # 腾讯DNS
        '8.8.8.8',          # Google DNS
        '1.1.1.1',          # Cloudflare DNS
        '8.8.4.4',          # Google DNS备用
        '208.67.222.222'    # OpenDNS
    ]
    current_dns_index = 0
    
    # 设置较短的超时时间，但增加重试次数
    resolver.timeout = 3
    resolver.lifetime = 5
    
    for attempt in range(max_retries):
        try:
            # 获取A记录（IPv4）
            if attempt == 0:
                print(f"\n域名 {domain} 的所有IP地址：")
            else:
                print(f"第{attempt + 1}次尝试解析 {domain}...")
            
            print("IPv4地址：")
            a_records = resolver.resolve(domain, 'A')
            for ip in a_records:
                print(f"- {ip}")
                result.append(f"{ip}#{region}")
            
            # 如果成功解析IPv4，尝试解析IPv6（可选）
            try:
                print("\nIPv6地址：")
                aaaa_records = resolver.resolve(domain, 'AAAA')
                for ip in aaaa_records:
                    print(f"- {ip}")
            except dns.resolver.NoAnswer:
                print("- 没有IPv6地址")
            except Exception:
                pass  # 忽略IPv6解析错误
            
            # 如果成功获取到IPv4地址，直接返回
            if result:
                return result
            
        except dns.resolver.NoAnswer:
            print(f"未找到域名 {domain} 的IP地址")
        except dns.resolver.NXDOMAIN:
            print(f"域名 {domain} 不存在")
            return []  # 域名不存在，无需重试
        except Exception as e:
            print(f"解析出错: {str(e)}")
        
        # 在重试前切换DNS服务器
        if current_dns_index < len(dns_servers):
            new_dns = dns_servers[current_dns_index]
            print(f"切换到DNS服务器: {new_dns}")
            resolver.nameservers = [new_dns]
            current_dns_index += 1
        
        # 短暂等待后重试
        time.sleep(0.5)
    
    print(f"在{max_retries}次尝试后仍无法解析域名 {domain}")
    return []

def save_results(results, filename="ip_list.txt"):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(f"{result}\n")
        print(f"\n结果已保存到 {filename}")
    except Exception as e:
        print(f"保存文件时出错: {str(e)}")

if __name__ == "__main__":
    try:
        # 加载配置
        config = load_config()
        
        # 创建解析器对象
        resolver = dns.resolver.Resolver()
        
        # 循环解析每个域名
        print("开始解析所有域名...")
        all_results = []
        for domain in config['domains']:
            results = get_all_domain_ips(domain, resolver)
            all_results.extend(results)
        
        # 保存结果到文件
        save_results(all_results)
        print("\n所有域名解析完成！")
        
    except ValueError as e:
        print(f"配置错误: {str(e)}")
    except Exception as e:
        print(f"程序出错: {str(e)}")
