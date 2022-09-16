use tinyvec::ArrayVec;
use crate::at::{AtRequest, AtResponse};

pub enum ApiFrame {
    Transmit64Request(Transmit64Request),
}

struct Transmit64Request {
    frame_id: u8,
    dest_addr: u64,
    options: u8,
    data: ArrayVec<[u8; 256]>
}

struct LocalATCommandRequest {
    frame_id: u8,
    at_command: AtRequest,
}

struct QueueLocalATCommandRequest {
    frame_id: u8,
    at_command: AtRequest,
}

struct TransmitRequest {
    frame_id: u8,
    dest_addr: u64,
    broadcast_radius: u8,
    options: u8,
    data: ArrayVec<[u8; 256]>
}

struct ExplicitAddressingCommandRequest {
    frame_id: u8,
    dest_addr: u64,
    source_endpoint: u8,
    dest_endpoint: u8,
    cluster_id: u16,
    profile_id: u16,
    broadcast_radius: u8,
    options: u8,
    data: ArrayVec<[u8; 256]>
}

struct RemoteATCommandRequest {
    frame_id: u8,
    dest_addr: u64,
    options: u8,
    at_command: AtRequest,
}

struct SecureRemoteATCommandRequest {
    frame_id: u8,
    password: ArrayVec<[u8; 33]>,
    dest_addr: u64,
    options: u8,
    at_command: AtRequest,
}

struct ModemStatus {
    status: u8
}

struct ExtendedTransmitStatus {
    frame_id: u8,
    transmit_retry_count: u8,
    delivery_status: u8,
    discovery_status: u8
}

struct RouteInformation {
    source_event: u8,
    timestamp: u32,
    ack_timeout_count: u8,
    tx_blocked_count: u8, 
    dest_addr: u64,
    source_addr: u64,
    responder_addr: u64,
    reciever_addr: u64
}

struct AggregateAddressingUpdate {
    new_addr: u64,
    old_addr: u64
}

struct Receive64Packet {
    source_addr: u64,
    rssi: u8,
    options: u8,
    data: ArrayVec<[u8; 256]>
}

struct LocalATCommandResponse {
    frame_id: u8,
    at_command: AtResponse,
    command_status: u8
}

struct TransmitStatus {
    frame_id: u8,
    status: u8
}

struct ReceivePacket {
    source_addr: u64,
    options: u8,
    data: ArrayVec<[u8; 256]>
}

struct ExplicitRecieveIndicator {
    source_addr: u64,
    source_endpoint: u8,
    dest_endpoint: u8,
    cluster_id: u16,
    profile_id: u16,
    options: u8,
    data: ArrayVec<[u8; 256]>
}

struct NodeIdentifierIndicator {
    source_addr: u64,
    options: u8,
    remote_address: u64,
    id_string: ArrayVec<[u8; 20]>,
    network_device_type: u8,
    source_event: u8,
    digi_profile_id: u16,
    digi_manufacturer_id: u16,
    // TODO: Optional device type identifier
    // TODO: Optional RSSI
}

struct RemoteATCommandResponse {
    frame_id: u8,
    source_addr: u64,
    at_command: AtResponse,
    command_status: u8
}