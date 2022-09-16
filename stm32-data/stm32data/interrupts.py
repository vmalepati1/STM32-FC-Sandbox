from stm32data.util import *
from glob import glob
import xmltodict
import re
import os


chip_interrupts = {}


def get(nvic_name, nvic_version, core):
    return chip_interrupts[(nvic_name, nvic_version)]


def parse():
    print("parsing interrupts")
    for f in sorted(glob('sources/cubedb/mcu/IP/NVIC*_Modes.xml')):
        if 'STM32MP1' in f:
            continue
        f = f.replace(os.path.sep, '/')
        ff = removeprefix(f, 'sources/cubedb/mcu/IP/')
        ff = removesuffix(ff, '_Modes.xml')

        [nvic_name, nvic_version] = ff.split('-')

        irqs = {}
        r = xmltodict.parse(open(f, 'rb'))

        xml_irqs = next(filter(lambda x: x['@Name'] == 'IRQn', r['IP']['RefParameter']))
        for irq in xml_irqs['PossibleValue']:
            value = irq['@Value']
            parts = value.split(':')

            # Interrupt name
            name = removesuffix(parts[0], "_IRQn")

            # Fix typo in STM32Lxx and L083 devices
            if name == "AES_RNG_LPUART1" and "RNG" not in str(parts[1:]):
                name = "AES_LPUART1"

            if name in irqs:
                continue

            print(f'{name:25} {nvic_version:12} {nvic_name:5}  {parts[1]:8} {parts[2]:45} {parts[3]:45} {parts[4]:15}')
            # Flags.
            # Y
            #   unknown, it's in all of them
            # H3, nHS
            #   ???
            # 2V, 3V, nV, 2V1
            #   unknown, it has to do with the fact the irq is shared among N peripehrals
            # DMA, DMAL0, DMAF0, DMAL0_DMAMUX, DMAF0_DMAMUX
            #   special format for DMA
            # DFSDM
            #   special format for DFSDM
            # EXTI
            #   special format for EXTI
            flags = parts[1].split(',')

            # F100xE MISC_REMAP remaps some DMA IRQs, so ST decided to give two names
            # to the same IRQ number.
            if nvic_version == 'STM32F100E' and name == 'DMA2_Channel4_5':
                continue

            # F3 can remap USB IRQs, ignore them.
            if nvic_version.startswith('STM32F3') and 'remap' in irq['@Comment']:
                continue

            signals = set()

            if name in ['NonMaskableInt', 'HardFault', 'MemoryManagement', 'BusFault', 'UsageFault', 'SVCall', 'DebugMonitor', 'PendSV', 'SysTick']:
                pass
            elif any(f in flags for f in ['DMA', 'DMAL0', 'DMAF0', 'DMAL0_DMAMUX', 'DMAF0_DMAMUX']):
                dmas = parts[3].split(',')
                chans = parts[4].split(';')
                assert len(dmas) == len(chans)
                for i in range(len(dmas)):
                    dma = dmas[i]
                    if ',' in chans[i]:
                        ch_from, ch_to = chans[i].split(',')
                    else:
                        ch_from = chans[i]
                        ch_to = chans[i]
                    ch_from = int(ch_from)
                    ch_to = int(ch_to)
                    for ch in range(ch_from, ch_to+1):
                        signals.add((dma, f'CH{ch}'))
            elif name == 'DMAMUX1':  # TODO does DMAMUX have more irq signals? seen in U5
                signals.add(('DMAMUX1', 'OVR'))
            elif name == 'DMAMUX1_S':  # TODO does DMAMUX have more irq signals? seen in U5
                signals.add(('DMAMUX1', 'OVR'))
            elif name == 'DMAMUX_OVR':
                signals.add(('DMAMUX1', 'OVR'))
            elif name == 'DMAMUX1_OVR':
                signals.add(('DMAMUX1', 'OVR'))
            elif name == 'DMAMUX2_OVR':
                signals.add(('DMAMUX2', 'OVR'))
            elif 'DMAMUX' in flags:
                assert False  # should've been handled above
            elif 'EXTI' in flags:
                for signal in parts[2].split(','):
                    signals.add(('EXTI', signal))
            elif name == 'FLASH':
                signals.add(('FLASH', 'GLOBAL'))
            elif name == 'CRS':
                signals.add(('RCC', 'CRS'))
            elif name == 'RCC':
                signals.add(('RCC', 'GLOBAL'))
            else:
                if parts[2] == '':
                    continue

                peri_names = parts[2].split(',')

                name2 = name
                if name2 == 'USBWakeUp':
                    name2 = 'USB_WKUP'
                if name2 == 'USBWakeUp_RMP':
                    name2 = 'USB_WKUP'
                if name2.endswith('_S'):
                    name2 = removesuffix(name2, '_S')

                peri_signals = {p: [] for p in peri_names}

                curr_peris = None
                if len(peri_names) == 1:
                    curr_peris = peri_names

                # Parse IRQ signals from the IRQ name.
                for part in tokenize_name(name2):
                    if part == 'TAMPER':
                        part = 'TAMP'

                    if part == 'LSECSS':
                        signals.add(('RCC', 'LSECSS'))
                    elif part == 'CSS':
                        signals.add(('RCC', 'CSS'))
                    elif part == 'LSE':
                        signals.add(('RCC', 'LSE'))
                    elif part == 'CRS':
                        signals.add(('RCC', 'CRS'))
                    elif pp := match_peris(peri_names, part):
                        curr_peris = pp
                    else:
                        assert curr_peris is not None
                        for p in curr_peris:
                            peri_signals[p].append(part)

                for p, ss in peri_signals.items():
                    known = valid_signals(p)

                    # If we have no signals for the peri, assume it's "global" so assign it all known ones
                    if ss == []:
                        if p.startswith('COMP'):
                            ss = ['WKUP']
                        else:
                            ss = known

                    for s in ss:
                        if s not in known:
                            raise Exception(f'Unknown signal {s} for peri {p}, known={known}')
                        signals.add((p, s))

            for (peri, signal) in signals:
                print(f'    {peri}:{signal}')
            irqs[name] = signals

        irqs2 = {}
        for name, signals in irqs.items():
            for (p, s) in signals:
                irqs2.setdefault(p, []).append({
                    'signal': s,
                    'interrupt': name,
                })

        for p, pirqs in irqs2.items():
            psirqs = {}
            for irq in pirqs:
                psirqs.setdefault(irq['signal'], []).append(irq['interrupt'])
            for s, irqs in psirqs.items():
                if len(irqs) != 1:
                    print(f'DUPE: {p} {s} {irqs}')

        chip_interrupts[(nvic_name, nvic_version)] = irqs2


def tokenize_name(name):
    # Treat IRQ names are "tokens" separated by `_`, except some tokens
    # contain `_` themselves, such as `C1_RX`.
    r = re.compile('(SPDIF_RX|EP\d+_(IN|OUT)|OTG_FS|OTG_HS|USB_FS|C1_RX|C1_TX|C2_RX|C2_TX|[A-Z0-9]+(_\d+)*)_*')

    name = name.upper()

    res = []
    i = 0
    while i < len(name):
        m = r.match(name, i)
        assert m is not None
        res.append(m.group(1))
        i = m.end()
    return res


PERI_OVERRIDE = {
    'USB_FS':   ['USB'],
    'OTG_HS':   ['USB_OTG_HS'],
    'OTG_FS':   ['USB_OTG_FS'],
    'USB':      ['USB_DRD_FS'],
    'UCPD1_2':  ['UCPD1', 'UCPD2'],
    'ADC1':     ['ADC'],
    'CEC':      ['HDMI_CEC'],
    'SPDIF_RX': ['SPDIFRX1', 'SPDIFRX'],
    'CAN1':     ['CAN'],
    'TEMP':     ['TEMPSENS'],
    'DSI':      ['DSIHOST'],
    'HRTIM1':   ['HRTIM'],
    'GTZC':     ['GTZC_S'],
    'TZIC':     ['GTZC_S'],
}


def match_peris(peris, name):
    if over := PERI_OVERRIDE.get(name):
        res = []
        for p in over:
            if p in peris:
                res.append(p)
        if len(res) != 0:
            return res

    res = []
    if m := re.fullmatch('(I2C|[A-Z]+)(\d+(_\d+)*)', name):
        name = m.group(1)
        for n in m.group(2).split('_'):
            p = f'{name}{n}'
            if p not in peris:
                return []
            res.append(p)
    else:
        for p in peris:
            if p == name or (p.startswith(name) and re.fullmatch('\d+', removeprefix(p, name))):
                res.append(p)

    return res


def merge_peri_irq_signals(peri_irqs, additional):
    for key, value in additional.items():
        if key not in peri_irqs:
            peri_irqs[key] = []
        peri_irqs[key].append(value)


irq_signals_map = {
    'CAN': ['TX', 'RX0', 'RX1', 'SCE'],
    'FDCAN': ['IT0', 'IT1', 'CAL'],
    'I2C': ['ER', 'EV'],
    'FMPI2C': ['ER', 'EV'],
    'TIM': ['BRK', 'UP', 'TRG', 'COM', 'CC'],
    'HRTIM': ['Master', 'TIMA', 'TIMB', 'TIMC', 'TIMD', 'TIME', 'TIMF'],
    'RTC': ['ALARM', 'WKUP', 'TAMP', 'STAMP', 'SSRU'],
    'SUBGHZ': ['RADIO'],
    'IPCC': ['C1_RX', 'C1_TX', 'C2_RX', 'C2_TX'],
    'HRTIM': ['MASTER', 'TIMA', 'TIMB', 'TIMC', 'TIMD', 'TIME', 'TIMF', 'FLT'],
    'COMP': ['WKUP', 'ACQ'],
    'RCC': ['RCC', 'CRS'],
    'MDIOS': ['GLOBAL', 'WKUP'],
    'ETH': ['GLOBAL', 'WKUP'],
    'LTDC': ['GLOBAL', 'ER'],
    'DFSDM': ['FLT0', 'FLT1', 'FLT2', 'FLT3', 'FLT4', 'FLT5', 'FLT6', 'FLT7'],
    'MDF': ['FLT0', 'FLT1', 'FLT2', 'FLT3', 'FLT4', 'FLT5', 'FLT6', 'FLT7'],
    'PWR': ['S3WU'],
    'GTZC': ['GLOBAL', 'ILA'],
    'WWDG': ['GLOBAL', 'RST'],

    'USB_OTG_FS': ['GLOBAL', 'EP1_OUT', 'EP1_IN', 'WKUP'],
    'USB_OTG_HS': ['GLOBAL', 'EP1_OUT', 'EP1_IN', 'WKUP'],
    'USB': ['LP', 'HP', 'WKUP'],
}


def valid_signals(peri):
    for prefix, signals in irq_signals_map.items():
        if peri.startswith(prefix):
            return signals
    return ['GLOBAL']


def filter_interrupts(peri_irqs, all_irqs):
    return [
        i for i in peri_irqs if i['interrupt'] in all_irqs
    ]
