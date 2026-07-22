import os

from N2G import drawio_diagram

styles_dir = os.environ.get('STYLES')

diagram = drawio_diagram()
diagram.add_diagram("Page-1")
diagram.add_node(id="VBRBACKUPSERVER01",label="VBRBACKUPSERVER01",style=styles_dir+"/VBRBACKUPSERVER.txt",x_pos="-470",y_pos="710",width="60",height="60",data={"ip": "192.168.207.100","role":"VBRBACKUPSERVER","other_roles":"VBRCONSOLE"})
diagram.add_node(id="VBRREPOLINUX01",label="VBRREPOLINUX01",style=styles_dir+"/VBRBACKUPREPOSITORYLINUX.txt",x_pos="-230",y_pos="390",width="60",height="60",data={"ip": "192.168.203.100","role":"VBRBACKUPREPOSITORYLINUX","other_roles":"VBRBACKUPREPOSITORY"})
diagram.add_node(id="VBRREPOWIN01",label="VBRREPOWIN01",style=styles_dir+"/VBRPOWERNFS.txt",x_pos="200",y_pos="210",width="60",height="60",data={"ip": "192.168.204.100","role":"VBRPOWERNFS","other_roles":"VBRBACKUPREPOSITORY,VBRBACKUPREPOSITORYWINDOWS,VBRMOUNTSERVER"})
diagram.add_node(id="VBRWANACCELERATOR01",label="VBRWANACCELERATOR01",style=styles_dir+"/VBRWANACCELERATOR.txt",x_pos="-640",y_pos="210",width="60",height="60",data={"ip": "4.4.4.4","role":"VBRWANACCELERATOR","other_roles":""})
diagram.add_node(id="VBRWANACCELERATOR02",label="VBRWANACCELERATOR02",style=styles_dir+"/VBRWANACCELERATOR.txt",x_pos="-360",y_pos="280",width="60",height="60",data={"ip": "5.5.5.5","role":"VBRWANACCELERATOR","other_roles":""})
diagram.add_link("VBRBACKUPSERVER01","VBRREPOLINUX01",src_label="2500 to 3300",trgt_label="22, 6160, 6162, 2500 to 3300")
diagram.add_link("VBRBACKUPSERVER01","VBRREPOWIN01",src_label="9401",trgt_label="135, 445, 6160, 6161, 6162, 6170, 2500 to 3300, 49152 to 65535")
diagram.add_link("VBRBACKUPSERVER01","VBRWANACCELERATOR01",trgt_label="135, 445, 6160, 6162, 6164, 6220, 49152 to 65535")
diagram.add_link("VBRBACKUPSERVER01","VBRWANACCELERATOR02",trgt_label="135, 445, 6160, 6162, 6164, 6220, 49152 to 65535")
diagram.add_link("VBRREPOWIN01","VBRREPOLINUX01",src_label="2500 to 3300",trgt_label="2500 to 3300")
diagram.add_link("VBRWANACCELERATOR01","VBRREPOLINUX01",trgt_label="2500 to 3300")
diagram.add_link("VBRWANACCELERATOR01","VBRREPOWIN01",trgt_label="2500 to 3300")
diagram.add_link("VBRWANACCELERATOR01","VBRWANACCELERATOR02",src_label="6164, 6165",trgt_label="6164, 6165")
diagram.add_link("VBRWANACCELERATOR02","VBRREPOLINUX01",trgt_label="2500 to 3300")
diagram.add_link("VBRWANACCELERATOR02","VBRREPOWIN01",trgt_label="2500 to 3300")
diagram.dump_file(filename="repo1.drawio", folder="./")
