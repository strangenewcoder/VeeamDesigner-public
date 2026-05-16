import os

from N2G import drawio_diagram

styles_dir = os.environ.get('STYLES')

diagram = drawio_diagram()
diagram.add_diagram("Page-1")
diagram.add_node(id="VBRBACKUPSERVER01",label="VBRBACKUPSERVER01",style=styles_dir+"/VBRBACKUPSERVER.txt",x_pos="230",y_pos="200",width="60",height="60",data={"ip": "192.168.207.100","role":"VBRBACKUPSERVER","other_roles":"VBRCONSOLE"})
diagram.add_node(id="VBRREPOWIN01",label="VBRREPOWIN01",style=styles_dir+"/VBRPOWERNFS.txt",x_pos="400",y_pos="400",width="60",height="60",data={"ip": "192.168.204.100","role":"VBRPOWERNFS","other_roles":"VBRBACKUPREPOSITORY,VBRBACKUPREPOSITORYWINDOWS,VBRMOUNTSERVER"})
diagram.add_link("VBRBACKUPSERVER01","VBRREPOWIN01",src_label="9401",trgt_label="135, 445, 6160, 6161, 6162, 6170, 2500 to 3300, 49152 to 65535")
diagram.dump_file(filename="site_a.drawio", folder="./")
