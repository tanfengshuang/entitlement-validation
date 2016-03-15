#!/bin/sh

usage() {
    echo "Usage: $0 cdn|CDN|rhn|RHN|sat|SAT"
    exit 1
}

get_ip() {
    ip_file="$WORKSPACE/RESOURCES.txt"
    if [ -f "$ip_file" ]; then
        System_IP=`cat $ip_file | grep EXISTING_NODES  | awk -F '=' '{print $2}'`
        if [ "$System_IP" != "" ]; then
            export System_IP=$System_IP
            echo "Succeed to get beaker IP: $System_IP."
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
    echo "Rlease_Version=$Rlease_Version"

    cdn_test_case_path=$WORKSPACE/entitlement-validation/CDN/Tests/
    cdn_test_suite=$WORKSPACE/entitlement-validation/test_cdn.py
    cdn_case_template=$WORKSPACE/entitlement-validation/CDN/case_template/CDNEntitlement_template.py

    # Generate all test cases from template for cdn testing, and add test cases to test suite
    OLD_IFS="$IFS"
    IFS=","
    PID_array=($PID)
    IFS="$OLD_IFS"
    for pid in ${PID_array[@]}
    do
        echo "Ready to generate test case for PID $pid"
        case_name=CDNEntitlement_${pid}
        case_full_name=${cdn_test_case_path}${case_name}.py

        # Generate test case
        cp $cdn_case_template $case_full_name
        sed -i -e "s/PID/$pid/g" -e "s/VARIANT/$Variant/g" -e "s/ARCH/$Arch/g" $case_full_name

        # Add import sentence to __init__.py
        if [ "`cat $cdn_test_suite | grep $case_name`" ==  "" ]; then sed -i "2a\from CDN.Tests.$case_name import $case_name" $cdn_test_suite; fi

        # Add test cases to test suite
        line="suite.addTest(CDNEntitlement_${pid}('testCDNEntitlement_${pid}'))"
        if [ "`cat $cdn_test_suite | grep $case_name | grep -v import`" == "" ]; then sed -i "/suite = unittest.TestSuite()/a\    $line" $cdn_test_suite; fi
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

    rhn_test_case=$WORKSPACE/entitlement-validation/RHN/Tests/RHNEntitlement.py
    rhn_test_suite=$WORKSPACE/entitlement-validation/test_rhn.py

    # Replace VARIANT and ARCH in rhn test suite and test case
    sed -i -e "s/VARIANT/$Variant/g" -e "s/ARCH/$Arch/g" $rhn_test_case $rhn_test_suite
}

prepare_sat() {
    echo "waiting for the implement..."
    # Trying to get beaker ip
    get_ip

    # Print params
    echo "Variant=$Variant"
    echo "Arch=$Arch"
    echo "Manifest_URL=$Manifest_URL"
    echo "Distro=$Distro"
    echo "SAT5_Server=$SAT5_Server"

    sat5_test_case=$WORKSPACE/entitlement-validation/SAT5/Tests/SAT5Entitlement.py
    sat5_test_suite=$WORKSPACE/entitlement-validation/test_sat5.py

    # Replace VARIANT and ARCH in rhn test suite and test case
    sed -i -e "s/VARIANT/$Variant/g" -e "s/ARCH/$Arch/g" $sat5_test_case $sat5_test_suite
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
