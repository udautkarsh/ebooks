#!/usr/bin/env python3

from subprocess import Popen,PIPE
exclude_is = ['jenkins-agent-nodejs','jenkins','jenkins-agent-maven']
registry_server = 'registry.ocp4.lab.com:5000'
def run_command(cmd):

    try:
        p = Popen(cmd, stdout=PIPE,stderr=PIPE, shell=True)
        out, err = p.communicate()
        rc = p.returncode
        status=(rc, out.decode(), err.decode())
        return(status)
    except Exception as e:
        log.error(str(e))
        return False

def findAllImageStreams():
    cmd="oc describe co openshift-samples | grep imagestreams | cut -d ':' -f 3 | cut -d ';' -f 1"	
    return_status=run_command(cmd) 
    if return_status[0]:
        print(f"COMMAND EXECUTION FAILED ===> {cmd}")	
        exit(1)
    is_list = return_status[1].split()
    is_list = list(set(is_list) - set(exclude_is))
    print("\n")
    print(f"Total number of ImageStream: {len(is_list)}")
    print("=================================\n")
    return is_list
    
def imageISMapping(is_list):

    is_mapping={}
    for _is in is_list:
        cmd=f"oc get is {_is} -n openshift -o json | jq .spec.tags[].from.name | grep registry.redhat.io"
        return_status = run_command(cmd)
        is_mapping[_is] = return_status[1].strip().split()
    return is_mapping
    print("IMAGE STREAM AND ITS RELATED IMAGES:")
    for key, value in is_mapping.items():
        print("\n\n")
        print("----------------------------------------------------------------------------------------------")
        print(f"ImageStream ====> {key}")
        print("    ------------------------------------------------------------------------------------------")
        for item in value:
            print(f"    {item}")
        print("----------------------------------------------------------------------------------------------")


def mirrorImages(is_mapping):
    total_is_count = len(is_mapping.keys())
    mirrored_is_count=0
    for _is, images in is_mapping.items():
        mirrored_is_count += 1
        image_count = len(images)  
        mirrored_image_count = 1
        for image in images:

            print(f"IMAGESTREAM   :===> {_is:<40}  IS Image Status: ({mirrored_image_count}/{image_count})   IS Status: ({mirrored_is_count}/{total_is_count})")
            print("-------------------------------------------------------------------------------------------------------------------------")
            image=image.strip('"')
            cmd=f'docker pull {image}'
            print(f"Pulling Image :===> {cmd}")
            return_status=run_command(cmd)
            if return_status[0]:
                print("Pulling failed :===> {image}")
                continue
            cmd = f"docker images -q {image}"
            return_status=run_command(cmd)
            
            image_id = return_status[1].strip()
            image = "/".join(image.split('/')[1:])
            local_repo = f"{registry_server}/{image}"
            cmd = f"docker tag {image_id} {local_repo}"
            print(f"Tagging Image :===> {cmd}")             
            return_status=run_command(cmd)
            if return_status[0]:
                print("Tagging failed :===> {image}")
                continue

            cmd=f"docker push {local_repo}"
            print(f"Pushing Image :===> {cmd}")
            return_status=run_command(cmd)
            if return_status[0]:
                print("Pushing failed :===> {image}")
                continue

            mirrored_image_count += 1
            print("\n\n")
            

def main():
    is_list = findAllImageStreams()
    is_mapping = imageISMapping(is_list)
    mirrorImages(is_mapping)

main()
