import os

from N2G import drawio_diagram

styles_dir = os.environ.get('STYLES')

diagram = drawio_diagram()
diagram.add_diagram("Page-1")
diagram.add_node(id="VBRBACKUPSERVER01",label="VBRBACKUPSERVER01",style=styles_dir+"/VBRBACKUPSERVER.txt",x_pos="230",y_pos="250",width="60",height="60",data={"ip": "192.168.207.100","role":"VBRBACKUPSERVER","other_roles":"VBRCONSOLE"})
diagram.add_node(id="VBRREPOLINUX01",label="VBRREPOLINUX01",style=styles_dir+"/VBRBACKUPREPOSITORYLINUX.txt",x_pos="414",y_pos="410",width="60",height="60",data={"ip": "192.168.207.101","role":"VBRBACKUPREPOSITORYLINUX","other_roles":""})
diagram.add_link("VBRBACKUPSERVER01","VBRREPOLINUX01",src_label="2500 to 3300",trgt_label="22, 6160, 6162, 2500 to 3300")
diagram.dump_file(filename="site_b.drawio", folder="./")
