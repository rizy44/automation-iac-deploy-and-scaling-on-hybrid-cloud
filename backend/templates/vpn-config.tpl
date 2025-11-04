================================================================================
AWS Site-to-Site VPN Configuration for OpenStack SD-WAN Edge
================================================================================

TUNNEL 1 Configuration:
-----------------------
AWS VPN Endpoint:        ${tunnel1_address}
Customer Gateway IP:     ${tunnel1_cgw_inside_address}/30
AWS Gateway IP:          ${tunnel1_vgw_inside_address}/30
Pre-shared Key:          ${tunnel1_preshared_key}

TUNNEL 2 Configuration:
-----------------------
AWS VPN Endpoint:        ${tunnel2_address}
Customer Gateway IP:     ${tunnel2_cgw_inside_address}/30
AWS Gateway IP:          ${tunnel2_vgw_inside_address}/30
Pre-shared Key:          ${tunnel2_preshared_key}

BGP Configuration:
------------------
AWS BGP ASN:             ${aws_bgp_asn}
Customer BGP ASN:        ${customer_bgp_asn}

Network Routes:
---------------
OpenStack Network:       ${openstack_cidr}

================================================================================
StrongSwan Configuration Commands:
================================================================================

1. Install StrongSwan on your OpenStack VM:
   sudo apt-get update && sudo apt-get install -y strongswan

2. Configure /etc/ipsec.conf:
   (See openstack-edge-setup.md for detailed configuration)

3. Configure /etc/ipsec.secrets:
   ${tunnel1_address} : PSK "${tunnel1_preshared_key}"
   ${tunnel2_address} : PSK "${tunnel2_preshared_key}"

4. Start StrongSwan:
   sudo systemctl restart strongswan
   sudo ipsec statusall

================================================================================

