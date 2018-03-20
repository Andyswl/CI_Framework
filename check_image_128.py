import SSHLibrary
import time
import re,os,sys
import string


def check_image(L1,L2,version):
    index = ["OAM","Cell","cCP","UE"]
    s_ip = "10.159.215.166"
    s_name = "root"
    s_pass = "btsci"
    ip = "10.68.138.128"
    op_name = "admin"
    op_pass = "btsci"
    s = SSHLibrary.SSHLibrary()
    s.open_connection(s_ip)
    s.login(s_name,s_pass)
    s.set_client_configuration(timeout=10,prompt="#")
    s.write("cat /mnt/%s/%s/%s/Internal_Use/%s.md5sum" %(L1, L2, version, version))
    sum=s.read_until_prompt()
    print sum
    s.close_connection()
    c = SSHLibrary.SSHLibrary(timeout=3600)
    c.open_connection(ip)
    c.login(op_name, op_pass)
    c.set_client_configuration(prompt="$")
    c.write("cd /volume1/CloudBTS/CBTS18;mkdir %s" %version)
    c.read_until_prompt()
    c.set_client_configuration(timeout=600,prompt="password:")
    c.write("scp root@10.159.215.166:/mnt/%s/%s/%s/Internal_Use/%s_release_BTSSM_downloadable.zip  /volume1/CloudBTS/CBTS18/%s/%s_release_BTSSM_downloadable.zip"  %(L1,L2,version,version,version,version))
    c.read_until_prompt()
    c.write(op_pass)
    c.set_client_configuration(timeout=600,prompt="password:")
    c.write("scp -r root@10.159.215.166:/mnt/%s/%s/%s/Internal_Use/CBAM  /volume1/CloudBTS/CBTS18/%s/CBAM"%(L1,L2,version,version))
    c.read_until_prompt()
    c.write(op_pass)
    for var in index:
        c.set_client_configuration(timeout=600,prompt="password:")
        c.write("scp root@10.159.215.166:/mnt/%s/%s/%s/Internal_Use/%s_%s.qcow2  /volume1/CloudBTS/CBTS18/%s/%s_%s.qcow2"  %(L1,L2,version,version,var,version,version,var))
        c.read_until_prompt()
        c.write(op_pass)
        c.set_client_configuration(timeout=600,prompt="$")
        c.read_until_prompt()
        c.set_client_configuration(timeout=10,prompt="$")
        c.write("md5sum /volume1/CloudBTS/CBTS18/%s/%s_%s.qcow2" %(version,version,var))
        txt = c.read_until_prompt()
        test = txt.split(" ")[0]
        print test
        n = sum.find(test)
        #print n
        i = 0
        while (i<3 and n == -1):
            print "please wait....."
            c.set_client_configuration(timeout=600,prompt="password:")
            c.write("scp root@10.159.215.166:/mnt/%s/%s/%s/Internal_Use/%s_%s.qcow2  /volume1/CloudBTS/CBTS18/%s/%s_%s.qcow2"  %(L1,L2,version,version,var,version,version,var))
            c.read_until_prompt()
            c.write(op_pass)
            c.set_client_configuration(timeout=600,prompt="$")
            c.read_until_prompt()
            c.set_client_configuration(timeout=10,prompt="$")
            c.write("md5sum /volume1/CloudBTS/CBTS18/%s/%s_%s.qcow2" %(version,version,var))
            txt = c.read_until_prompt()
            test = txt.split(" ")[0]
            print test
            n = sum.find(test)
            #print  "Again"+n
            i = i+1
    c.close_connection()

if __name__ == "__main__":
    Pre_Branch = sys.argv[1]
    Branch = sys.argv[2]
    Verison = sys.argv[3]
    check_image(Pre_Branch,Branch,Verison)
