import requests
import ipaddress

GITHUB_IPS_CACHE = None

def get_github_actions_ips():
    global GITHUB_IPS_CACHE
    if GITHUB_IPS_CACHE is not None:
        return GITHUB_IPS_CACHE

    response = requests.get("https://api.github.com/meta")
    response.raise_for_status()
    meta = response.json()

    # Return ipaddress.IPv4Network/IPv6Network
    GITHUB_IPS_CACHE = [ipaddress.ip_network(ip) for ip in meta.get("actions", [])]
    return GITHUB_IPS_CACHE

def verify_ip_whitelist(client_ip):
    if not client_ip:
        return False

    try:
        client_ip_addr = ipaddress.ip_address(client_ip)
    except ValueError:
        return False

    github_ips = get_github_actions_ips()

    for github_ip in github_ips:
        if client_ip_addr in github_ip:
            return True

    return False