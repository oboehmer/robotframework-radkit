*** Settings ***
Documentation    Acceptance tests for RADKit Robot Framework library
...              These tests verify keyword discovery and basic argument handling.
...              They use a mocked RADKit backend (no real RADKit service needed).
Library          RADKit
Library          Collections

*** Test Cases ***
Library Can Be Imported
    [Documentation]    Verify the RADKit library can be imported
    Log    RADKit library imported successfully

Client Version Returns String
    [Documentation]    Test that RADKit Client Version returns a string
    ${version}=    RADKit Client Version
    Should Not Be Empty    ${version}

Set And Get Timeout
    [Documentation]    Test that timeout can be set and returns old value
    ${old}=    RADKit timeout    60
    Should Be Equal As Numbers    ${old}    300
    ${old2}=    RADKit timeout    300
    Should Be Equal As Numbers    ${old2}    60
