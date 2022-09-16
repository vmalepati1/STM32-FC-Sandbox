mod frames;
mod at;

use nom::combinator::verify;
use nom::error::Error;
use nom::number::complete::u8;
use nom::number::streaming::be_u16 as s_be_u16;
use nom::number::streaming::u8 as s_u8;
use nom::{bytes::streaming::tag as s_tag, IResult};
use nom::{
    bytes::{complete::tag, streaming::take as s_take},
    character::complete::char,
    combinator::rest_len,
    number::complete::{be_u64, be_u8},
};
use tinyvec::ArrayVec;
use frames::ApiFrame;

// Start by searching for 0x7E in buffer.
// Parse the next two bytes as length.
// Take the next n bytes as frame_data.
// Parse the next byte as checksum.
// Verify checksum.
// If checksum passes, frame_data is good. Remove all these bytes from buffer.
// If checksum fails, search until next 0x7E. Keep that byte and the rest.

fn frame_data(input: &[u8]) -> IResult<&[u8], &[u8]> {
    let (input, tag) = s_tag([0x7E])(input)?;
    let (input, length) = s_be_u16(input)?;
    let (input, frame_data) = s_take(length)(input)?;
    let (input, checksum) = verify(s_u8, |checksum| verify_checksum(frame_data, *checksum))(input)?;

    Ok((input, frame_data))
}

fn verify_checksum(frame_data: &[u8], checksum: u8) -> bool {
    let sum = frame_data.iter().fold(0u8, |x, y| x.wrapping_add(*y)) + checksum;
    sum == 0xFF
}



fn transmit_request_64(input: &[u8]) -> IResult<&[u8], ApiFrame> {
    let (input, frame_type) = tag([0x00])(input)?;
    let (input, frame_id) = be_u8(input)?;
    let (input, dest_addr) = be_u64(input)?;
    let (input, options) = be_u8(input)?;

    let (payload, payload_len) = verify(rest_len, |x| x <= &256)(input)?;

    let mut payload_vec: ArrayVec<[u8; 256]> = ArrayVec::new();
    payload_vec.extend_from_slice(payload);

    todo!()
    // Ok((&[], ApiFrame::TransmitRequest64(frame_id, dest_addr, options, payload_vec)))
}
