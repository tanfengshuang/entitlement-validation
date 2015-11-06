#!/bin/sh

environment_path="$WORKSPACE/entitlement-validation/Utils/environment.py"
test_suite_path=$WORKSPACE/entitlement-validation/test_entitlement.py
test_case_path=$WORKSPACE/entitlement-validation/Tests/
cdn_case_template=${test_case_path}CDN_Entitlement_template.py
init_file=${test_case_path}__init__.py

usage() {
    echo "Usage: $0 cdn|CDN|rhn|RHN|sat|SAT"
    exit 1
}

get_ip() {
    ip_file="RESOURCES.txt"
    if [ -f "$ip_file" ]; then
        BEAKER_IP=`cat $WORKSPACE/RESOURCES.txt | grep EXISTING_NODES  | awk -F '=' '{print $2}'`
        if [ "$BEAKER_IP" != "" ]; then
            if [ "`cat $environment_path | grep BEAKER_IP`" == "" ]; then echo "BEAKER_IP = $BEAKER_IP" >> $environment_path; fi
            echo "Succeed to get the ip of beaker system: $BEAKER_IP"
        else
            echo "ERROR: Failed to get the ip of beaker system!"
            exit 1
        fi
    else
        echo "ERROR: $ip_file does not exist, Failed to get the ip of beaker system!"
        exit 1
fi
}

prepare_cdn() {
    # trying to get beaker ip
    #get_ip

    # write testing parameters to environment.py
    echo "writing testing parameters into file environment.py"
    if [ "`cat $environment_path | grep MANIFEST_URL`" == "" ]; then echo "MANIFEST_URL = $MANIFEST_URL" >> $environment_path; fi
    if [ "`cat $environment_path | grep PID`" == "" ]; then echo "PID = $PID" >> $environment_path; fi
    if [ "`cat $environment_path | grep VARIANT`" == "" ]; then echo "VARIANT = $VARIANT" >> $environment_path; fi
    if [ "`cat $environment_path | grep ARCH`" == "" ]; then echo "ARCH = $ARCH" >> $environment_path; fi
    if [ "`cat $environment_path | grep DISTRO`" == "" ]; then echo "DISTRO = $DISTRO" >> $environment_path; fi
    if [ "`cat $environment_path | grep CDN`" == "" ]; then echo "CDN = $CDN" >> $environment_path; fi
    if [ "`cat $environment_path | grep CANDLEPIN`" == "" ]; then echo "CANDLEPIN = $CANDLEPIN" >> $environment_path; fi

    # generate all test cases from template for cdn testing, and add test cases to test suite
    OLD_IFS="$IFS"
    IFS=","
    PID_array=($PID)
    IFS="$OLD_IFS"
    for pid in ${PID_array[@]}
    do
        echo "Ready to generate test case for PID $pid"
        case_name=CDN_Entitlement_$pid
        case_full_name=${case_path}CDN_Entitlement_$pid.py

        # generate test case
        cp $cdn_case_template $case_full_name
        sed -i -e "s/PID/$pid/g" $case_full_name

        # add import sentence to __init__.py
        if [ "`cat $init_file | grep $case_name`" ==  "" ]; then echo "from $case_name import $case_name" >> $init_file; fi

        # and add test cases to test suite
        line="suite.addTest(CDN_Entitlement_$pid('test_CDN_Entitlement'))"
        if [ "`cat $test_suite_path | grep $case_name`" == "" ]; then sed -i "/suite = unittest.TestSuite()/a\    $line" $test_suite_path; fi
    done
}

prepare_rhn() {
    echo "waiting for the implement..."
}

prepare_sat() {
    echo "waiting for the implement..."
}

if [ $# -eq 1 ] ; then
    param=$1
    case $param in
        cdn | CDN)
            echo "call function prepare_cdn"
            prepare_cdn;;
        rhn | RHN)
            echo "call function prepare_rhn"
            prepare_rhn;;
        sat | SAT)
            echo "call function prepare_sat"
            prepare_sat;;
        *)
            usage;;
    esac
else
    usage
fi
