import os

from N2G import drawio_diagram

styles_dir = os.environ.get('STYLES')

diagram = drawio_diagram()
diagram.add_diagram("Page-1")
diagram.add_node(id="ESXI01",label="ESXI01",style=styles_dir+"/VMWAREESXI.txt",x_pos="40",y_pos="480",width="60",height="60",data={"ip": "192.168.210.100","role":"VMWAREESXI","other_roles":"VMWAREESXICDP"})
diagram.add_node(id="ESXI02",label="ESXI02",style=styles_dir+"/VMWAREESXI.txt",x_pos="700",y_pos="480",width="60",height="60",data={"ip": "3.3.3.3","role":"VMWAREESXI","other_roles":"VMWAREESXICDP"})
diagram.add_node(id="VBRBACKUPSERVER01",label="VBRBACKUPSERVER01",style=styles_dir+"/VBRBACKUPSERVER.txt",x_pos="370",y_pos="670",width="60",height="60",data={"ip": "192.168.207.100","role":"VBRBACKUPSERVER","other_roles":""})
diagram.add_node(id="VBRCDPPROXY01",label="VBRCDPPROXY01",style=styles_dir+"/VBRCDPPROXY.txt",x_pos="40",y_pos="210",width="60",height="60",data={"ip": "1.1.1.1","role":"VBRCDPPROXY","other_roles":""})
diagram.add_node(id="VBRCDPPROXY02",label="VBRCDPPROXY02",style=styles_dir+"/VBRCDPPROXY.txt",x_pos="700",y_pos="210",width="60",height="60",data={"ip": "2.2.2.2","role":"VBRCDPPROXY","other_roles":""})
diagram.add_node(id="VC01",label="VC01",style=styles_dir+"/VMWAREVCENTER.txt",x_pos="370",y_pos="60",width="60",height="60",data={"ip": "192.168.209.100","role":"VMWAREVCENTER","other_roles":"VMWAREVCENTERCDP"})
diagram.add_link("VBRBACKUPSERVER01","VBRCDPPROXY01",src_label="33034",trgt_label="6182")
diagram.add_link("VBRBACKUPSERVER01","VBRCDPPROXY02",src_label="33034",trgt_label="6182")
diagram.add_link("VBRBACKUPSERVER01","ESXI01",src_label="33034, 33035",trgt_label="443, 902, 33035")
diagram.add_link("VBRBACKUPSERVER01","ESXI02",src_label="33034, 33035",trgt_label="443, 902, 33035")
diagram.add_link("VBRBACKUPSERVER01","VC01",src_label="33034, 33035",trgt_label="443")
diagram.add_link("ESXI01","VBRCDPPROXY01",src_label="902, 33032",trgt_label="33032")
diagram.add_link("ESXI01","VBRCDPPROXY02",src_label="902, 33032",trgt_label="33032")
diagram.add_link("ESXI01","ESXI02",src_label="33033, 33034, 33035, 33036, 33038, 33039",trgt_label="33033, 33034, 33035, 33036, 33038, 33039")
diagram.add_link("ESXI02","VBRCDPPROXY01",src_label="902, 33032",trgt_label="33032")
diagram.add_link("ESXI02","VBRCDPPROXY02",src_label="902, 33032",trgt_label="33032")
diagram.add_link("VBRCDPPROXY01","VBRCDPPROXY02",src_label="33033",trgt_label="33033")
diagram.add_link("VBRCDPPROXY01","VC01",trgt_label="443")
diagram.add_link("VBRCDPPROXY02","VC01",trgt_label="443")
diagram.dump_file(filename="cdp1.drawio", folder="./")
