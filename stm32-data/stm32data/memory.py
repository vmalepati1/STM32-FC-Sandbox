import sys
import re
import xmltodict
from glob import glob
from stm32data.util import *


def splat_names(base, parts):
    names = []
    for part in parts:
        if part.startswith("STM32"):
            names.append(base)
        elif part.startswith(base[5]):
            names.append('STM32' + part)
        else:
            names.append(base[0: len(base) - len(part)] + part)

    return names


def split_names(str):
    cleaned = []
    names = str.split("/")
    current_base = None
    for name in names:
        name = name.split(' ')[0].strip()
        if '-' in name:
            parts = name.split('-')
            current_base = parts[0]
            splatted = splat_names(current_base, parts)
            current_base = splatted[0]
            cleaned = cleaned + splatted
        elif name.startswith("STM32"):
            current_base = name
            cleaned.append(name)
        elif name.startswith(current_base[5]):
            names.append('STM32' + name)
        else:
            cleaned.append(current_base[0: len(current_base) - len(name)] + name)
    return cleaned


memories = []


def parse():
    for f in sorted(glob('sources/cubeprogdb/db/*.xml')):
        # print("parsing ", f);
        device = xmltodict.parse(open(f, 'rb'))['Root']['Device']
        device_id = device['DeviceID']
        name = device['Name']
        names = split_names(name)
        flash_size = None
        flash_addr = None
        write_size = None
        erase_size = None
        erase_value = None
        ram_size = None
        ram_addr = None

        for peripheral in device['Peripherals']['Peripheral']:
            if peripheral['Name'] == 'Embedded SRAM' and ram_size is None:
                configs = peripheral['Configuration']
                if type(configs) != list:
                    configs = [configs]
                ram_addr = int(configs[0]['Parameters']['@address'], 16)
                ram_size = int(configs[0]['Parameters']['@size'], 16)
                #print( f'ram {addr} {size}')
            if peripheral['Name'] == 'Embedded Flash' and flash_size is None:
                configs = peripheral['Configuration']
                if type(configs) != list:
                    configs = [configs]
                flash_addr = int(configs[0]['Parameters']['@address'], 16)
                flash_size = int(configs[0]['Parameters']['@size'], 16)
                erase_value = int(peripheral['ErasedValue'], 16)
                write_size = int(configs[0]['Allignement'], 16)
                bank = configs[0]['Bank']
                if type(bank) != list:
                    bank = [bank]
                fields = bank[0]['Field']
                if type(fields) != list:
                    fields = [fields]

                erase_size = int(fields[0]['Parameters']['@size'], 16)
                for field in fields:
                    # print("Field", field)
                    erase_size = max(erase_size, int(field['Parameters']['@size'], 16))
                    #print( f'flash {addr} {size}')

        chunk = {
            'device-id': int(device_id, 16),
            'names': names,
        }

        if ram_size is not None:
            chunk['ram'] = {
                'address': ram_addr,
                'bytes': ram_size,
            }

        if flash_size is not None:
            chunk['flash'] = {
                'address': flash_addr,
                'bytes': flash_size,
                'erase_value': erase_value,
                'write_size': write_size,
                'erase_size': erase_size,
            }

        memories.append(chunk)

    # The chips below are missing from cubeprogdb
    memories.append({
        'device-id': 0,
        'names': ['STM32F302xD'],
        'ram': {
            'address': 0x20000000,
            'bytes': 64*1024,
        },
        'flash': {
            'address': 0x08000000,
            'bytes': 384*1024,
            'erase_value': 0xFF,
            'write_size': 8,
            'erase_size': 2048,
        }
    })
    memories.append({
        'device-id': 0,
        'names': ['STM32F303xD'],
        'ram': {
            'address': 0x20000000,
            'bytes': 80*1024,
        },
        'flash': {
            'address': 0x08000000,
            'bytes': 384*1024,
            'erase_value': 0xFF,
            'write_size': 8,
            'erase_size': 2048,
        }
    })
    memories.append({
        'device-id': 0,
        'names': ['STM32L100x6'],
        'ram': {
            'address': 0x20000000,
            'bytes': 32*1024,
        },
        'flash': {
            'address': 0x08000000,
            'bytes': 4*1024,
            'erase_value': 0xFF,
            'write_size': 4,
            'erase_size': 256,
        }
    })


def determine_ram_size(chip_name):
    for each in memories:
        for name in each['names']:
            if is_chip_name_match(name, chip_name):
                return each['ram']['bytes']
    raise Exception(f'could not find ram size for {chip_name}')


def determine_flash_size(chip_name):
    for each in memories:
        for name in each['names']:
            if is_chip_name_match(name, chip_name):
                return each['flash']['bytes']
    raise Exception(f'could not find flash size for {chip_name}')


def determine_flash_settings(chip_name):
    for each in memories:
        for name in each['names']:
            if is_chip_name_match(name, chip_name):
                return {
                    'erase_size': each['flash']['erase_size'],
                    'write_size': each['flash']['write_size'],
                    'erase_value': each['flash']['erase_value'],
                }
    raise Exception(f'could not find flash settings for {chip_name}')


def determine_device_id(chip_name):
    for each in memories:
        for name in each['names']:
            if is_chip_name_match(name, chip_name):
                return each['device-id']
    return None


def is_chip_name_match(pattern, chip_name):
    chip_name = chip_name.replace("STM32F479", "STM32F469")  # F479 is missing, it's the same as F469.
    chip_name = chip_name.replace("STM32G050", "STM32G051")  # same...
    chip_name = chip_name.replace("STM32G060", "STM32G061")  # same...
    chip_name = chip_name.replace("STM32G070", "STM32G071")  # same...
    chip_name = chip_name.replace("STM32G0B0", "STM32G0B1")  # same...
    chip_name = chip_name.replace("STM32G4A", "STM32G49")  # same...
    chip_name = chip_name.replace("STM32L422", "STM32L412")  # same...
    chip_name = chip_name.replace("STM32WB30", "STM32WB35")  # same...
    pattern = pattern.replace('x', '.')
    return re.match(pattern + ".*", chip_name)
