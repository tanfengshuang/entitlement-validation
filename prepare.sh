#!/bin/sh

test_case_path=$WORKSPACE/entitlement-validation/Tests/
cdn_test_suite_path=$WORKSPACE/entitlement-validation/test_cdn.py
cdn_case_template=${test_case_path}CDNEntitlement_template.py

usage() {
    echo "Usage: $0 cdn|CDN|rhn|RHN|sat|SAT"
    exit 1
}

get_ip() {
    ip_file="$WORKSPACE/RESOURCES.txt"
    if [ -f "$ip_file" ]; then
        Beaker_IP=`cat $ip_file | grep EXISTING_NODES  | awk -F '=' '{print $2}'`
        if [ "$Beaker_IP" != "" ]; then
            export Beaker_IP=$Beaker_IP
            echo "Succeed to get beaker IP: $Beaker_IP."
        else
            echo "ERROR: Failed to get the IP of beaker system!"
            exit 1
        fi
    else
        echo "ERROR: $ip_file does not exist, Failed to get the ip of beaker system!"
        exit 1
fi
}

prepare_cdn() {
    # Trying to get beaker ip
    get_ip

    if [ "$PID" == "" ]; then
        # Get PID from manifest for current arch and varaint
        python $WORKSPACE/entitlement-validation/analyze_testing.py pid
        PID=`cat PID.txt`
    fi

    # Print params
    echo "PID=$PID"
    echo "Variant=$Variant"
    echo "Arch=$Arch"
    echo "Manifest_URL=$Manifest_URL"
    echo "Distro=$Distro"
    echo "CDN=$CDN"
    echo "Candlepin=$Candlepin"
    echo "Blacklist=$Blacklist"
    echo "Rlease_Version=$Rlease_Version"

    # Generate all test cases from template for cdn testing, and add test cases to test suite
    OLD_IFS="$IFS"
    IFS=","
    PID_array=($PID)
    IFS="$OLD_IFS"
    for pid in ${PID_array[@]}
    do
        echo "Ready to generate test case for PID $pid"
        case_name=CDNEntitlement_$pid
        case_full_name=${test_case_path}CDNEntitlement_$pid.py

        # Generate test case
        cp $cdn_case_template $case_full_name
        sed -i -e "s/PID/$pid/g" $case_full_name

        # Add import sentence to __init__.py
        if [ "`cat $cdn_test_suite_path | grep $case_name`" ==  "" ]; then sed -i "2a\from Tests.$case_name import $case_name" $cdn_test_suite_path; fi

        # Add test cases to test suite
        line="suite.addTest(CDNEntitlement_$pid('testCDNEntitlement'))"
        if [ "`cat $cdn_test_suite_path | grep $case_name | grep -v import`" == "" ]; then sed -i "/suite = unittest.TestSuite()/a\    $line" $cdn_test_suite_path; fi
    done
}

prepare_rhn() {
    # Trying to get beaker ip
    get_ip

    # Print params
    echo "Variant=$Variant"
    echo "Arch=$Arch"
    echo "Manifest_URL=$Manifest_URL"
    echo "Distro=$Distro"
    echo "RHN=$RHN"
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
