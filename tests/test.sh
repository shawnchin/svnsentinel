#!/bin/bash

BASEDIR=$(dirname $0)
REPO="${BASEDIR}/repos/"
CFG="${BASEDIR}/test_config.py"
CMD="${BASEDIR}/../precommit.py"
RUN="${CMD} $REPO -c ${CFG} -r "

LOG="test.log"
date > $LOG  # reset log file. prepend date

TESTS=(
  # "rev_id  expected_rc test_label..."
    "2  0 Adding file outside restricted path"
    "4  0 Editing file outside restricted path"
    "5  1 Adding file within restricted path"
    "3  1 Editing file within restricted path"
    "6  0 Testing bypass mechanism"
    "7  1 Addding file within restricted path (not in e_list)"
    "8  1 Adding dir matching root of an item in e_list"
    "9  0 Adding file to path covered by e_list"
    "12 1 Braching from valid source to invalid destination"
    "14 1 Braching from invalid source to valid destination"
    "16 0 Braching from valid source to valid destination"
    "17 0 Braching from valid source to valid destination (wildcard)"
    "18 1 Braching from invalid source to valid destination (wildcard)"
    "19 0 Branching outside restricted path"
    "25 1 Valid branching followed by restricted edits"
    "20 1 Move from invalid source to valid destination"
    "21 1 Move from valid source to invalid destination"
    "24 0 Move from valid source to valid destination"
    "23 0 Move outside restricted path"
    "31 0 Valid merge"
    "32 1 Valid merge followed by manual edits"
    "33 1 Propset on restricted path"
)

TEST_FAILED=0
TEST_COUNT=0

function run_test {
    REV=$1; shift
    EXPECT=$1; shift
    LABEL=$*
    CMD="${RUN} ${REV}"
    (( TEST_COUNT++ ))

    echo "#${TEST_COUNT}" >> $LOG
    echo "Running $CMD" >> $LOG
    OUT=$($CMD 2>&1)
    RET=$?
    
    echo " - expecting rc ${EXPECT}, got ${RET}" >> $LOG
    if [[ $OUT != "" ]]; then
        echo " - STDERR:" >> $LOG
        echo "$OUT" >> $LOG
    fi

    echo -n "${TEST_COUNT}. ${LABEL} -- "
    if [[ $RET -ne $EXPECT ]]; then
        echo -e "\e[01;31mFAIL\e[00m"
        (( TEST_FAILED++ ))
    else
        echo -e "\e[01;32mPASS\e[00m"
    fi
    
}

echo "TESTING SVNSENTINEL"
echo "==================="
echo "REPO: ${REPO}"
echo

for i in "${TESTS[@]}"; do
    run_test $i
done

echo ""
echo "------------------------------------------"
echo -n "     ${TEST_COUNT} tests. "
if [[ ${TEST_FAILED} -ne 0 ]]; then
    echo -en "\e[01;31m"  # RED
fi
echo -e "${TEST_FAILED} failed\e[00m."
exit $TEST_FAILED
