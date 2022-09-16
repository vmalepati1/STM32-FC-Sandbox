#![macro_use]

#[cfg_attr(adc_v4, path = "v4.rs")]
#[cfg_attr(adc_v3, path = "v3.rs")]
#[cfg_attr(adc_v2, path = "v2.rs")]
#[cfg_attr(adc_g0, path = "v3.rs")]
#[cfg_attr(adc_f1, path = "f1.rs")]
#[cfg_attr(adc_v1, path = "v1.rs")]
mod _version;

#[allow(unused)]
pub use _version::*;

use crate::peripherals;

pub(crate) mod sealed {
    pub trait Instance {
        fn regs() -> &'static crate::pac::adc::Adc;
        #[cfg(all(not(adc_f1), not(adc_v1)))]
        fn common_regs() -> &'static crate::pac::adccommon::AdcCommon;
    }

    #[cfg(all(not(adc_f1), not(adc_v1)))]
    pub trait Common {
        fn regs() -> &'static crate::pac::adccommon::AdcCommon;
    }

    pub trait AdcPin<T: Instance> {
        fn channel(&self) -> u8;
    }
}

#[cfg(not(adc_f1))]
pub trait Instance: sealed::Instance + 'static {}
#[cfg(adc_f1)]
pub trait Instance: sealed::Instance + crate::rcc::RccPeripheral + 'static {}
#[cfg(all(not(adc_f1), not(adc_v1)))]
pub trait Common: sealed::Common + 'static {}
pub trait AdcPin<T: Instance>: sealed::AdcPin<T> {}

#[cfg(not(stm32h7))]
foreach_peripheral!(
    (adc, $inst:ident) => {
        impl crate::adc::sealed::Instance for peripherals::$inst {
            fn regs() -> &'static crate::pac::adc::Adc {
                &crate::pac::$inst
            }
            #[cfg(all(not(adc_f1), not(adc_v1)))]
            fn common_regs() -> &'static crate::pac::adccommon::AdcCommon {
                foreach_peripheral!{
                    (adccommon, $common_inst:ident) => {
                        return &crate::pac::$common_inst
                    };
                }
            }
        }

        impl crate::adc::Instance for peripherals::$inst {}
    };
);

#[cfg(stm32h7)]
foreach_peripheral!(
    (adc, ADC3) => {
        impl crate::adc::sealed::Instance for peripherals::ADC3 {
            fn regs() -> &'static crate::pac::adc::Adc {
                &crate::pac::ADC3
            }
            #[cfg(all(not(adc_f1), not(adc_v1)))]
            fn common_regs() -> &'static crate::pac::adccommon::AdcCommon {
                foreach_peripheral!{
                    (adccommon, ADC3_COMMON) => {
                        return &crate::pac::ADC3_COMMON
                    };
                }
            }
        }

        impl crate::adc::Instance for peripherals::ADC3 {}
    };
    (adc, $inst:ident) => {
        impl crate::adc::sealed::Instance for peripherals::$inst {
            fn regs() -> &'static crate::pac::adc::Adc {
                &crate::pac::$inst
            }
            #[cfg(all(not(adc_f1), not(adc_v1)))]
            fn common_regs() -> &'static crate::pac::adccommon::AdcCommon {
                foreach_peripheral!{
                    (adccommon, ADC_COMMON) => {
                        return &crate::pac::ADC_COMMON
                    };
                }
            }
        }

        impl crate::adc::Instance for peripherals::$inst {}
    };
);

#[cfg(all(not(adc_f1), not(adc_v1)))]
foreach_peripheral!(
    (adccommon, $inst:ident) => {
        impl sealed::Common for peripherals::$inst {
            fn regs() -> &'static crate::pac::adccommon::AdcCommon {
                &crate::pac::$inst
            }
        }

        impl crate::adc::Common for peripherals::$inst {}
    };
);

macro_rules! impl_adc_pin {
    ($inst:ident, $pin:ident, $ch:expr) => {
        impl crate::adc::AdcPin<peripherals::$inst> for crate::peripherals::$pin {}

        impl crate::adc::sealed::AdcPin<peripherals::$inst> for crate::peripherals::$pin {
            fn channel(&self) -> u8 {
                $ch
            }
        }
    };
}
