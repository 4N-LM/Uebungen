from scapy.all import *

# DHCPv6-Solicit-Nachricht erstellen
dhcpv6_solicit = IPv6(dst="ff02::1:2") / UDP(sport=546, dport=547) / DHCP6_Solicit()

print("[*] Sende DHCPv6 Solicit...")
response = sr1(dhcpv6_solicit, timeout=5)

if response:
    print("[+] Antwort vom DHCPv6-Server erhalten!")
    response.show()
else:
    print("[-] Keine Antwort erhalten.")
