import os

from N2G import drawio_diagram

styles_dir = os.environ.get('STYLES')

diagram = drawio_diagram()
diagram.add_diagram("Page-1")
diagram.add_node(id="VBRBACKUPSERVER01",label="VBRBACKUPSERVER01",style=styles_dir+"/VBRBACKUPSERVER.txt",x_pos="260",y_pos="437",width="60",height="60",data={"ip": "192.168.207.100","role":"VBRBACKUPSERVER","other_roles":"VBRCONSOLE"})
diagram.add_node(id="VBRCONSOLE01",label="VBRCONSOLE01",style=styles_dir+"/VBRCONSOLE.txt",x_pos="20",y_pos="340",width="60",height="60",data={"ip": "192.168.202.100","role":"VBRCONSOLE","other_roles":""})
diagram.add_node(id="VBRREPOWIN01",label="VBRREPOWIN01",style=styles_dir+"/VBRPOWERNFS.txt",x_pos="260",y_pos="210",width="60",height="60",data={"ip": "192.168.204.100","role":"VBRPOWERNFS","other_roles":"VBRBACKUPREPOSITORY,VBRBACKUPREPOSITORYWINDOWS,VBRMOUNTSERVER"})
diagram.add_node(id="VEEAMAI",label="VEEAMAI",style=styles_dir+"/VEEAMAI.txt",x_pos="140",y_pos="630",width="60",height="60",data={"ip": "veeamuai","role":"VEEAMAI","other_roles":""})
diagram.add_node(id="VEEAMLICENSE",label="VEEAMLICENSE",style=styles_dir+"/VEEAMLICENSE.txt",x_pos="440",y_pos="437",width="60",height="60",data={"ip": "veeamlicense","role":"VEEAMLICENSE","other_roles":""})
diagram.add_node(id="VEEAMUPDATE",label="VEEAMUPDATE",style=styles_dir+"/VEEAMUPDATE.txt",x_pos="390",y_pos="630",width="60",height="60",data={"ip": "veeamupdate","role":"VEEAMUPDATE","other_roles":""})
diagram.add_node(id="VEEAMUPDATESIGNATURE",label="VEEAMUPDATESIGNATURE",style=styles_dir+"/VEEAMUPDATESIGNATURE.txt",x_pos="260",y_pos="50",width="60",height="60",data={"ip": "vbrupfatesignature","role":"VEEAMUPDATESIGNATURE","other_roles":""})
diagram.add_link("VBRBACKUPSERVER01","VBRREPOWIN01",src_label="9401",trgt_label="135, 445, 6160, 6161, 6162, 6170, 2500 to 3300, 49152 to 65535")
diagram.add_link("VBRBACKUPSERVER01","VEEAMLICENSE",trgt_label="80, 443")
diagram.add_link("VBRBACKUPSERVER01","VEEAMUPDATE",trgt_label="443")
diagram.add_link("VBRBACKUPSERVER01","VEEAMAI",trgt_label="443")
diagram.add_link("VBRREPOWIN01","VEEAMUPDATESIGNATURE",trgt_label="443")
diagram.add_link("VBRCONSOLE01","VBRBACKUPSERVER01",trgt_label="8543, 8544, 8545, 9392, 9396, 9401, 9402, 9403, 9404, 9420, 10003, 20443")
diagram.add_link("VBRCONSOLE01","VBRREPOWIN01",trgt_label="2500 to 3300")
diagram.add_link("VBRCONSOLE01","VEEAMAI",trgt_label="443")
diagram.dump_file(filename="veeam.drawio", folder="./")
