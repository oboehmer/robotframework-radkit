*** Settings ***
Library     RADKitLibrary
Library    Collections
Library    String
Library    OperatingSystem
Library     pyats.robot.pyATSRobot
Library     unicon.robot.UniconRobot
Suite Setup    Check and Set Environment
Test Setup       connect as radkit client
Test Teardown    Run Keywords    RADKit disconnect    AND    Sleep    1
Variables    ${CURDIR}${/}smoke_variables.yaml

*** Variables ***
${RADKIT_SECRET_PASSWORD: Secret}    %{RADKIT_CLIENT_PRIVATE_KEY_PASSWORD}
${RADKIT_TESTBED}      ${CURDIR}${/}testbed.yaml

*** Test Cases ***
Test RADkit version
    [Setup]
    ${version}=   RADKit Client Version
    Should be True    re.match(r'\\d+\.\\d+', $version)
    [Teardown]

Connect to RadKit linux device via unicon in lab ${RADKIT_SERVICE_SN}
    [Tags]   radkit-interactive
    [Setup]      Run Keywords        use testbed "${RADKIT_TESTBED}"    AND    connect to device "${RADKIT_LINUX_DEVICE}"
    ${result}=   execute "${RADKIT_COMMAND}" on device "${RADKIT_LINUX_DEVICE}"
    Should Contain    ${result}    ${RADKIT_EXPECTED}
    ${result}=   execute "${RADKIT_COMMAND_2}" on device "${RADKIT_LINUX_DEVICE}"
    Should Contain    ${result}    ${RADKIT_EXPECTED_2}
    [Teardown]   disconnect from device "${RADKIT_LINUX_DEVICE}"

Test Radkit Inventory
    [Tags]   radkit-client
    RADKit select service     ${RADKIT_SERVICE_SN}
    ${inventory}=   RADKit device inventory
    Should be True   "${RADKIT_LINUX_DEVICE}" in $inventory
    ${inventory}=   RADKit device inventory     ${RADKIT_SERVICE_SN}    raw=True
    Should be True   "${RADKIT_LINUX_DEVICE}" in $inventory
    Should Be True   "DeviceDict" in str(type($inventory))
    ${inventory}=   RADKit device inventory     ${RADKIT_SERVICE_SN}    filter=name,mock.*1
    Should Be True   len($inventory)>0
    ${inventory}=   RADKit device inventory     ${RADKIT_SERVICE_SN}    filter=device_type,IOS
    Should Be True   len($inventory)>0

Test Radkit Select Device
    [Tags]   radkit-client
    RADKit select service     ${RADKIT_SERVICE_SN}
    check select devices    ${MULTIPLE_RADKIT_DEVICES}

    @{device_list}=   Evaluate   $MULTIPLE_RADKIT_DEVICES.split(";")
    check select devices    ${device_list}

    ${inventory}=   RADKit device inventory    filter=${RADKIT_DEVICE_FILTER}
    check select devices    ${inventory}

Test Radkit Execute
    [Tags]   radkit-client
    RADKit select service    ${RADKIT_SERVICE_SN}
    ${output}=   RADKit execute     ${RADKIT_COMMAND}   devices=${RADKIT_LINUX_DEVICE}
    Should be True    "${RADKIT_EXPECTED}" in $output["${RADKIT_LINUX_DEVICE}"]

Test Radkit Execute Raw
    [Tags]   radkit-client
    RADKit select service    ${RADKIT_SERVICE_SN}
    ${output}=   RADKit execute     ${RADKIT_COMMAND}   devices=${RADKIT_LINUX_DEVICE}    raw=True
    Should be True    $output.full_result[$RADKIT_LINUX_DEVICE][$RADKIT_COMMAND].data

Test Radkit Execute Multiple devices
    [Tags]   radkit-client    robot:recursive-continue-on-failure
    RADKit select service    ${RADKIT_SERVICE_SN}
    # test device1;device2;device3
    @{device_list}=   Evaluate   $MULTIPLE_RADKIT_DEVICES.split(";")
    ${output}=   RADKit execute     ${RADKIT_COMMAND}   devices=${MULTIPLE_RADKIT_DEVICES}
    check output   ${output}    @{device_list}
    # test list
    ${output}=   RADKit execute     ${RADKIT_COMMAND}   devices=${device_list}
    check output   ${output}    @{device_list}

Test Radkit Execute with radkit inventory input
    [Documentation]   test ability to work with RADKit inventory filters/subset
    [Tags]   radkit-client    robot:recursive-continue-on-failure
    RADKit select service    ${RADKIT_SERVICE_SN}
    ${subset}=   RADKit device inventory    filter=${RADKIT_DEVICE_FILTER}    raw=true
    ${output}=   RADKit execute     ${RADKIT_COMMAND}   devices=${subset}
    @{device_list}=    Evaluate   list($subset)
    check output   ${output}    @{device_list}

Test Radkit Execute Multiple commands
    [Tags]   radkit-client
    RADKit select service    ${RADKIT_SERVICE_SN}
    @{command_list}=   Create List   ${RADKIT_COMMAND}   ${RADKIT_COMMAND_2}
    ${output}=   RADKit execute     ${command_list}    devices=${RADKIT_LINUX_DEVICE}
    Should Contain   ${output}[${RADKIT_LINUX_DEVICE}][${RADKIT_COMMAND}]    ${RADKIT_EXPECTED}
    Should Contain   ${output}[${RADKIT_LINUX_DEVICE}][${RADKIT_COMMAND_2}]  ${RADKIT_EXPECTED_2}

Test Radkit Execute with responsive and nonresponsive devices
    [Tags]   radkit-client    robot:recursive-continue-on-failure
    RADKit select service    ${RADKIT_SERVICE_SN}
    @{device_list}=   Create List    ${RADKIT_LINUX_DEVICE}    ${UNRESPONSIVE_RADKIT_DEVICE}
    ${output}=   RADKit execute      ${RADKIT_COMMAND}   devices=${device_list}
    Should Contain   ${output}[${RADKIT_LINUX_DEVICE}]    ${RADKIT_EXPECTED}
    Should be True   ${output}[${UNRESPONSIVE_RADKIT_DEVICE}] is None

Test Radkit Execute Multiple commands with responsive and unresponsive device
    [Tags]   radkit-client
    RADKit select service    ${RADKIT_SERVICE_SN}
    @{device_list}=   Create List    ${RADKIT_LINUX_DEVICE}    ${UNRESPONSIVE_RADKIT_DEVICE}
    @{command_list}=   Create List   ${RADKIT_COMMAND}   ${RADKIT_COMMAND_2}
    ${output}=   RADKit execute     ${command_list}     devices=${device_list}
    Should Contain   ${output}[${RADKIT_LINUX_DEVICE}][${RADKIT_COMMAND}]    ${RADKIT_EXPECTED}
    Should Contain   ${output}[${RADKIT_LINUX_DEVICE}][${RADKIT_COMMAND_2}]  ${RADKIT_EXPECTED_2}
    Should be True   ${output}[${UNRESPONSIVE_RADKIT_DEVICE}][${RADKIT_COMMAND}] is None
    Should be True   ${output}[${UNRESPONSIVE_RADKIT_DEVICE}][${RADKIT_COMMAND_2}] is None

Test Radkit Execute with nonresponsive devices
    [Tags]   radkit-client    robot:recursive-continue-on-failure
    RADKit select service    ${RADKIT_SERVICE_SN}
    Run Keyword and Expect Error    *   RADKit execute      ${RADKIT_COMMAND}    devices=${UNRESPONSIVE_RADKIT_DEVICE}

Negative no connect
    [Tags]    radkit-client-negative   robot:continue-on-failure
    [Setup]     RADKit disconnect
    Run Keyword And Expect Error    *No authenticated cloud connection found*  RADKit select service    1234
    Run Keyword And Expect Error    *No RADkit service has been selected*    RADKit device inventory
    Run Keyword And Expect Error    *No service found with serial*    RADKit device inventory    1234
    Run Keyword And Expect Error    *No RADkit service has been selected*    RADKit execute      foo     devices=bar
    [Teardown]

Negative no select
    [Tags]    radkit-client-negative  robot:continue-on-failure
    Run Keyword And Expect Error    *No RADkit service has been selected*    RADKit device inventory
    Run Keyword And Expect Error    *No RADkit service has been selected*    RADKit execute      foo     devices=bar

Negative wrong select
    [Tags]    radkit-client-negative
    Run Keyword And Expect Error    *No service found with serial*    RADKit device inventory     9999
 
Test Radkit Genie Parse Single
    [Tags]   radkit-genie
    RADKit select service    ${RADKIT_SERVICE_SN}
    ${parsed}=   RADKit Genie Parse   commands=show version   devices=${RADKIT_IOSXE_DEVICE}    os=iosxe
    Should Be True    'version' in $parsed['${RADKIT_IOSXE_DEVICE}']['show version']

Test Radkit Genie Parse Raw
    [Tags]   radkit-genie
    RADKit select service    ${RADKIT_SERVICE_SN}
    ${raw_output}=   RADKit execute     show version   devices=${RADKIT_IOSXE_DEVICE}    raw=True
    ${parsed}=   RADKit Genie Parse   raw_output=${raw_output}    os=iosxe
    Should Be True    'version' in $parsed['${RADKIT_IOSXE_DEVICE}']['show version']

Test Radkit Genie Parse wihout OS
    # 1.7 derives the genie OS from radkit device type
    [Tags]   radkit-genie
    RADKit select service    ${RADKIT_SERVICE_SN}
    ${parsed}=   RADKit Genie Parse   commands=show version   devices=${RADKIT_IOSXE_DEVICE}
    Should Be True    'version' in $parsed['${RADKIT_IOSXE_DEVICE}']['show version']

Test Radkit Genie Parse Multiple Devices
    [Tags]   radkit-genie
    RADKit select service    ${RADKIT_SERVICE_SN}
    @{devices}=    Evaluate    $RADKIT_IOSXE_DEVICES.split(';')
    ${parsed}=   RADKit Genie Parse   commands=show version   devices=${devices}    os=iosxe
    FOR   ${device}    IN    @{devices}
        Should Be True    'version' in $parsed[$device]['show version']
    END

Test Radkit Genie Parse Multiple Devices and Commands
    [Tags]   radkit-genie    non-critical
    RADKit select service    ${RADKIT_SERVICE_SN}
    @{devices}=    Evaluate    $RADKIT_IOSXE_DEVICES.split(';')
    @{commands}=   Create List   show version    show interfaces
    ${parsed}=   RADKit Genie Parse   commands=${commands}    devices=${devices}    os=iosxe
    FOR   ${device}    IN    @{devices}
        FOR   ${command}    IN    @{commands}
            Should Be True    len($parsed[$device][$command]) > 0
        END
    END

Test Radkit Genie Parse with nonresponsive devices
    [Tags]   radkit-genie    non-critical
    RADKit select service    ${RADKIT_SERVICE_SN}
    @{devices}=    Evaluate    [$RADKIT_IOSXE_DEVICES.split(';')[0], $UNRESPONSIVE_RADKIT_DEVICE] 
    ${parsed}=    RADKit Genie Parse   commands=show version   devices=${devices}   os=iosxe
    Should be True    $parsed[$UNRESPONSIVE_RADKIT_DEVICE]['show version'] is None

Negative Test Radkit Genie Negative - commands and raw result
    [Tags]   radkit-genie    non-critical
    RADKit select service    ${RADKIT_SERVICE_SN}
    ${output}=   RADKit execute     show version   devices=${RADKIT_IOSXE_DEVICE}    raw=True
    Run Keyword and Expect Error
    ...    ValueError: either pass commands and devices OR the raw output from a previous RADKit Execute command, but not both
    ...    RADKit Genie Parse   commands=show version    raw_output=${output}    os=iosxe

Negative Test Radkit Genie Negative - no raw result
    [Tags]   radkit-genie    non-critical
    RADKit select service    ${RADKIT_SERVICE_SN}
    ${output}=   RADKit execute     show version   devices=${RADKIT_IOSXE_DEVICE}    raw=False
    Run Keyword and Expect Error
    ...    ValueError: expected argument is not a raw RADKit result*
    ...    RADKit Genie Parse   raw_output=${output}    os=iosxe

Test Radkit Genie Learn Single
    [Tags]   radkit-genie
    RADKit select service    ${RADKIT_SERVICE_SN}
    ${parsed}=   RADKit Genie Learn   devices=${RADKIT_IOSXE_DEVICE}   models=routing    os=iosxe
    Should be True    'info' in $parsed['${RADKIT_IOSXE_DEVICE}']['routing']

    @{models}=    Create List    routing
    ${parsed}=   RADKit Genie Learn   devices=${RADKIT_IOSXE_DEVICE}   models=${models}    os=iosxe
    Should be True    'info' in $parsed['${RADKIT_IOSXE_DEVICE}']['routing']

Test Radkit Genie Learn Multiple Devices
    [Tags]   radkit-genie    non-critical
    RADKit select service    ${RADKIT_SERVICE_SN}
    @{devices}=    Evaluate    $RADKIT_IOSXE_DEVICES.split(';')
    ${parsed}=   RADKit Genie Learn   devices=${devices}   models=routing    os=iosxe
    FOR   ${device}    IN    @{devices}
        Should Be True    'info' in $parsed[$device]['routing']
    END

Test Radkit Genie Learn Multiple Devices and Models
    [Tags]   radkit-genie    non-critical
    RADKit select service    ${RADKIT_SERVICE_SN}
    @{devices}=    Evaluate    $RADKIT_IOSXE_DEVICES.split(';')
    @{models}=   Create List   platform    routing
    ${parsed}=   RADKit Genie Learn   devices=${devices}   models=${models}    os=iosxe
    FOR   ${device}    IN    @{devices}
        FOR   ${model}    IN    @{models}
            Should Be True    len($parsed[$device][$model]) > 0
        END
    END

Test Radkit Genie Learn with nonresponsive devices
    [Tags]   radkit-genie    non-critical
    RADKit select service    ${RADKIT_SERVICE_SN}
    @{devices}=    Evaluate    [$RADKIT_IOSXE_DEVICES.split(';')[0], $UNRESPONSIVE_RADKIT_DEVICE]
    ${parsed}=    RADKit Genie Learn   devices=${devices}   models=routing    os=iosxe
    Should be True    $parsed[$UNRESPONSIVE_RADKIT_DEVICE]['routing'] is None

Test Radkit Genie Fingerprint
    [Tags]   radkit-genie    non-critical
    RADKit select service    ${RADKIT_SERVICE_SN}
    @{devices}=   Evaluate    $RADKIT_IOSXE_DEVICES.split(';')
    ${result}=    RADKit Genie Fingerprint    ${devices}

    ${parsed}=   RADKit Genie Parse   commands=show version   devices=${devices}
    FOR   ${device}    IN    @{devices}
        Should Be True    'version' in $parsed[$device]['show version']
    END

Test Radkit Genie Fingerprint with unresponsive device
    [Tags]   radkit-genie    non-critical
    RADKit select service    ${RADKIT_SERVICE_SN}
    @{devices}=    Evaluate    [$RADKIT_IOSXE_DEVICES.split(';')[0], $UNRESPONSIVE_RADKIT_DEVICE]
    ${result}=    RADKit Genie Fingerprint    ${devices}
    Should be True    $result[$UNRESPONSIVE_RADKIT_DEVICE] is None
    ${parsed}=   RADKit Genie Learn    devices=${devices}    models=platform    skip_unknown_os=True
    Should be True    len($parsed[$devices[0]]['platform']) > 0
    Should be True    $parsed[$UNRESPONSIVE_RADKIT_DEVICE]['platform'] is None

Test Radkit Port Fowarding dynamic port
    [Tags]   radkit-port-fwd
    RADKit select service    ${RADKIT_SERVICE_SN}
    ${forwarder}    ${port}=    RADKit Port Forward to Device    ${RADKIT_LINUX_DEVICE}    local_port=0    destination_port=22
    # check return types
    Should Be True    'RUNNING' in str($forwarder.status)
    Should Be True    1023 < $port < 65536

    # setting up another forwarder with the same local port should fail
    Run Keyword And Expect Error    *Address already in use*    RADKit Port Forward to Device    ${RADKIT_LINUX_DEVICE}    local_port=${port}    destination_port=22
    [Teardown]   Run Keywords
    ...    RADKit Stop Port Forward    ${forwarder}    AND
    ...    RADKit disconnect

Test Radkit Port Fowarding dynamic port with testbed change
    [Tags]   radkit-port-fwd
    use testbed "${RADKIT_TESTBED}"
    RADKit select service    ${RADKIT_SERVICE_SN}
    ${forwarder}    ${port}=    RADKit Port Forward to Device    ${RADKIT_LINUX_DEVICE}    local_port=0    destination_port=22    
    ...       testbed_device=${RADKIT_LINUX_DEVICE}    testbed_conn=cli
    connect to device "${RADKIT_LINUX_DEVICE}" via "cli"
    [Teardown]   Run Keywords
    ...    RADKit Stop Port Forward    ${forwarder}    AND
    ...    RADKit disconnect    AND
    ...    use testbed "${RADKIT_TESTBED}"

#  ## Resume not yet implemented, the below test fails
#  ## 
# Test Radkit Port Stop and Resume 
#     [Tags]   radkit-port-fwd
#     RADKit select service    ${RADKIT_SERVICE_SN}
#     ${forwarder}    ${port}=    RADKit Port Forward to Device    ${RADKIT_LINUX_DEVICE}    local_port=0    destination_port=22
#     ...       testbed_device=${RADKIT_LINUX_DEVICE}    testbed_conn=cli
#     connect to device "${RADKIT_LINUX_DEVICE}" via "cli"
#     disconnect from device "${RADKIT_LINUX_DEVICE}"
#     RADKit Stop Port Forward    ${forwarder}
#     Run Keyword And Expect Error    *    connect to device "${RADKIT_LINUX_DEVICE}" via "cli"
#     RADKit Resume Port Forward    ${forwarder}    testbed_device=${RADKIT_LINUX_DEVICE}    testbed_conn=cli
#     connect to device "${RADKIT_LINUX_DEVICE}" via "cli"
#     disconnect from device "${RADKIT_LINUX_DEVICE}"
#     [Teardown]   Run Keywords
#     ...    RADKit Stop Port Forward    ${forwarder}    AND
#     ...    RADKit disconnect    AND
#     ...    use testbed "${RADKIT_TESTBED}"

Test Radkit Port Fowarding Negative no service
    [Tags]   radkit-port-fwd
    [Setup]      RADKit disconnect
    Run Keyword And Expect Error    *No RADkit service has been selected*
    ...    RADKit Port Forward to Device    ${RADKIT_LINUX_DEVICE}    local_port=0    destination_port=22

Test Radkit Port Fowarding Negative illegal port
    [Tags]   radkit-port-fwd
    RADKit select service    ${RADKIT_SERVICE_SN}
    Run Keyword And Expect Error    ValueError: Destination port is not specified in port forwarding capabilities in the device
    ...    RADKit Port Forward to Device    ${RADKIT_LINUX_DEVICE}    local_port=0    destination_port=9999

Test Radkit Port Fowarding Negative testbed device or connection
    [Tags]   radkit-port-fwd
    RADKit select service    ${RADKIT_SERVICE_SN}
    Run Keyword And Expect Error    *required parameter when device is set*
    ...    RADKit Port Forward to Device    ${RADKIT_LINUX_DEVICE}    local_port=0    destination_port=22
    ...        testbed_device=${RADKIT_LINUX_DEVICE}
    Run Keyword And Expect Error    *is not defined in topology yaml file or has no connections attribute*
    ...    RADKit Port Forward to Device    ${RADKIT_LINUX_DEVICE}    local_port=0    destination_port=22
    ...        testbed_device=unknown_testbed_device    testbed_conn=cli
    Run Keyword And Expect Error    *is not defined in topology yaml file or has no connections attribute*
    ...    RADKit Port Forward to Device    ${RADKIT_LINUX_DEVICE}    local_port=0    destination_port=22
    ...        testbed_device=${RADKIT_LINUX_DEVICE}    testbed_conn=does_not_exist

Test Radkit Port Fowarding Negative port in use
    [Tags]   radkit-port-fwd
    RADKit select service    ${RADKIT_SERVICE_SN}
    ${forwarder}    ${port}=    RADKit Port Forward to Device    ${RADKIT_LINUX_DEVICE}    local_port=0    destination_port=22
    # setting up another forwarder with the same local port must fail
    Run Keyword And Expect Error    *Address already in use*
    ...    RADKit Port Forward to Device    ${RADKIT_LINUX_DEVICE}    local_port=${port}    destination_port=22
    [Teardown]   Run Keywords
    ...    RADKit Stop Port Forward    ${forwarder}    AND
    ...    RADKit disconnect

Test RADKit certificate login with password as Secret
    [Tags]   radkit-client
    [Setup]
    RADKit certificate login    domain=${RADKIT_DOMAIN}    private_key_password=${RADKIT_SECRET_PASSWORD}

Test RADKit certificate login with password as name of the environment variable
    [Tags]   radkit-client
    [Setup]
    RADKit certificate login    domain=${RADKIT_DOMAIN}    private_key_password=RADKIT_CLIENT_PRIVATE_KEY_PASSWORD

*** Keywords ***
Check and Set Environment
    Environment Variable Should Be Set    RADKIT_IDENTITY
    Environment Variable Should Be Set    RADKIT_CLIENT_PRIVATE_KEY_PASSWORD
    # service_sn is used in testbed.yaml, so it must be set in the environment
    Set Environment Variable    RADKIT_SERVICE_SN    ${RADKIT_SERVICE_SN}

check output
    [Arguments]   ${output}   @{device_list}
    FOR  ${dev}   IN   @{device_list}
        Should be True    "${RADKIT_EXPECTED}" in $output["${dev}"]
    END

load testbed and connect
    use testbed "${RADKIT_TESTBED}"
    connect to device "${RADKIT_LINUX_DEVICE}"
    connect to device "${RADKIT_IOSXE_DEVICE}"

connect as radkit client
    # identity/certs/etc. is taken from environment vars RADKIT_IDENTITY, RADKIT_CERT_PATH, RADKIT_KEY_PATH, RADKIT_CA_PATH
    Wait Until Keyword Succeeds    3x   5s
    ...    RADKit certificate login    domain=${RADKIT_DOMAIN}

check select devices
    [Arguments]    ${devices}
    ${devs}=   RADKit select devices    ${devices}
    ${res}=    Evaluate   ';'.join(sorted([d for d in $devs]))
    Should Be Equal    ${res}      ${MULTIPLE_RADKIT_DEVICES}
