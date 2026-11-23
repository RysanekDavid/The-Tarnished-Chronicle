use deku::prelude::*;

#[derive(PartialEq, Debug, DekuRead, DekuWrite)]
#[deku(ctx = "file_count: i32")]
pub(crate) struct Buckets {
    pub(crate) hash_offset: u64,
    pub(crate) bucket_count: i32,
    // These fields may have different values in older save versions
    pub(crate) bucket_header_size: u8,
    pub(crate) bucket_size: u8,
    pub(crate) hash_size: u8,
    unk0xf: u8,
    #[deku(count = "*bucket_count")]
    pub(crate) buckets: Vec<(u32, u32)>,
    #[deku(count = "file_count")]
    pub(crate) hashes: Vec<(u32, u32)>,
}
