import pytest
from plenum.common.txn_util import get_seq_no
from plenum.test.stasher import delay_rules_without_processing
from plenum.test.delayers import pDelay, cDelay
from plenum.test import waits
from sovtokenfees.test.helper import check_state, get_amount_from_token_txn, send_and_check_transfer, \
    send_and_check_nym_with_fees, ensure_all_nodes_have_same_data
from stp_core.loop.eventually import eventually
from plenum.test.helper import assertExp
from plenum.common.startable import Mode


def test_revert_xfer_and_other_txn_before_catchup(looper, helpers,
                                                  nodeSetWithIntegratedTokenPlugin,
                                                  fees_set, fees,
                                                  xfer_mint_tokens, xfer_addresses):
    nodes = nodeSetWithIntegratedTokenPlugin
    current_amount = get_amount_from_token_txn(xfer_mint_tokens)
    seq_no = get_seq_no(xfer_mint_tokens)
    lagging_node = nodes[-1]
    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, xfer_addresses,
                                                             current_amount)
    current_amount, seq_no, _ = send_and_check_transfer(helpers, xfer_addresses, fees, looper, current_amount, seq_no)
    with delay_rules_without_processing(lagging_node.nodeIbStasher, cDelay(), pDelay()):
        current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, xfer_addresses,
                                                                 current_amount)
        current_amount, seq_no, _ = send_and_check_transfer(helpers, xfer_addresses, fees, looper, current_amount, seq_no)
        looper.runFor(waits.expectedPrePrepareTime(len(nodes)))
        lagging_node.start_catchup()
        for n in nodes:
            looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))
        for n in nodes:
            looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))
    ensure_all_nodes_have_same_data(looper, nodes)
    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, xfer_addresses,
                                                             current_amount)
    current_amount, seq_no, _ = send_and_check_transfer(helpers, xfer_addresses, fees, looper, current_amount, seq_no)
    ensure_all_nodes_have_same_data(looper, nodes)
