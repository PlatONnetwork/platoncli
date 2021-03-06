import click
import sys
import os
import rlp
from hexbytes import HexBytes
from utility import get_command_usage, cust_print, read_json_file, g_dict_dir_config, get_eth_obj, get_time_stamp, \
    write_csv, write_QRCode
from common import verify_password, un_sign_data, check_dir_exits


def show_params():
    print('''
           类型      必填性         参数名称             参数解释
           int       must          typ                 金额类型
           int       must          amount              增持金额
           String    optional      node_id             节点ID
           dict      optional      transaction_cfg     交易基本配置
           ''')


@click.command(cls=get_command_usage("staking"))
@click.option('-f', '--file', help='The file is save params.')
@click.option('-d', '--address', help='wallet address.')
@click.option('-t', '--template', is_flag=True, default=False, help='View the increase staking parameter template. It is '
                                                                    'not effective to coexist with other parameters.')
@click.option('-c', '--config', default="",
              help='The configuration file specifying the IP and port of the '
                   'transaction to be sent. If it is configured in the global configuration network file, IP and prot '
                   'can be obtained by specifying the name in the configuration. If the network configuration is not '
                   'filled in.')
@click.option('-o', '--offline', is_flag=True, default=False,
              help='Offline transaction or offline transaction offline not input is the default '
                   'for online transaction, and a two-dimensional code picture is generated and '
                   'placed on the desktop, providing ATON offline scanning code signature.')
@click.option('-s', '--style', default="", help='This parameter is used to determine the type of file to be signed')
def increase(file, address, template, config, offline, style):
    """
    this is staking submodule increase command.
    """
    if template:
        show_params()
        return
    if not os.path.isfile(file):
        cust_print('file {} not exits! please check!'.format(file), fg='r')
        sys.exit(1)
    params = read_json_file(file)
    wallet_dir = g_dict_dir_config["wallet_dir"]
    wallet_file_path, private_key, hrp, _ = verify_password(address, wallet_dir)

    ppos = get_eth_obj(config, 'ppos')
    _params = {}
    try:
        _params['typ'] = params['typ']
        _params['node_id'] = params['node_id'] or ppos.admin.nodeInfo.id
        _params['amount'] = ppos.w3.toWei(str(params['amount']), "ether")
        _params['pri_key'] = private_key[2:]
        if isinstance(params['transaction_cfg'], dict):
            _params['transaction_cfg'] = params['transaction_cfg']
    except KeyError as e:
        cust_print('Key {} does not exist in file {},please check!'.format(e, file), fg='r')
        sys.exit(1)
    try:
        if offline:
            data = HexBytes(rlp.encode([rlp.encode(int(1002)), rlp.encode(bytes.fromhex(_params['node_id'])),
                                        rlp.encode(_params['typ']), rlp.encode(_params['amount'])])).hex()
            params['to_type'] = 'staking'
            transaction_dict = un_sign_data(data, params, ppos, _params['pri_key'])
            unsigned_tx_dir = g_dict_dir_config["unsigned_tx_dir"]
            check_dir_exits(unsigned_tx_dir)
            unsigned_file_csv_name = "unsigned_staking_increase_{}.csv".format(get_time_stamp())
            unsigned_file_path = os.path.join(unsigned_tx_dir, unsigned_file_csv_name)
            if style == '':
                write_csv(unsigned_file_path, [transaction_dict])
            else:
                unsigned_file_path = unsigned_file_path.replace('csv', 'jpg')
                write_QRCode(transaction_dict, unsigned_file_path)
            cust_print('unsigned_file save to:{}'.format(unsigned_file_path), fg='g')
        else:
            tx_hash = ppos.increaseStaking(*_params.values())
            cust_print('increase staking send transfer transaction successful, tx hash:{}.'.format(tx_hash), fg='g')
    except ValueError as e:
        cust_print('increase staking send transfer transaction fail,error info:{}'.format(e), fg='r')
        sys.exit(1)
