use std::io::Cursor;

use crate::regulation::regulation::{Regulation, RegulationIdentifier};
use deku::ctx::Endian;
use deku::prelude::*;
use deku::{DekuRead, DekuWrite};

use super::util::Util;

#[derive(PartialEq, Debug, DekuRead, DekuWrite)]
#[deku(
    endian = "endian",
    ctx = "endian: Endian, start: usize, file_size: usize, is_ps: bool"
)]
pub(crate) struct UserData11 {
    // Checksum (PC only)
    #[deku(skip, cond = "is_ps", count = "0x10")]
    checksum: Vec<u8>,

    // Magic
    magic: [u8; 4],

    unk0x4: u32,

    // Regulation Version
    pub(crate) version: u32,

    pub(crate) size: u32,

    #[deku(
        reader = "UserData11::read_regulation(
            deku::reader,
            *version,
            *size,
            file_size.saturating_sub(deku::byte_offset - start)
        )",
        writer = "UserData11::write_regulation(deku::writer, &self.regulation)"
    )]
    pub(crate) regulation: Option<Regulation>,

    #[deku(count = "file_size.saturating_sub(deku::byte_offset - start)")]
    rest: Vec<u8>,
}

impl UserData11 {
    /// Reads the regulation payload, or leaves it to `rest` when it is not
    /// needed or cannot be trusted. `available` is what is left of the BND4
    /// entry, so a garbage `size` in the inner header can never make the reader
    /// run past the block (issue #11: some 1.17.x saves declare sizes in the
    /// hundreds of MB there).
    fn read_regulation<R: std::io::Read>(
        reader: &mut deku::reader::Reader<R>,
        version: u32,
        size: u32,
        available: usize,
    ) -> Result<Option<Regulation>, DekuError> {
        let declared = size as usize;

        // Regulation (param data) is only needed for param editing; returning
        // None without reading lets `rest` keep the untouched bytes.
        if crate::save::save::skip_regulation() {
            return Ok(None);
        }
        if declared > available {
            eprintln!(
                "Warning: Skipping regulation: header declares {declared} bytes but the block has {available}"
            );
            return Ok(None);
        }
        // Version 11001000 and older have a different BND4 structure
        if version < 11210015 {
            eprintln!("Warning: Skipping regulation due to older save version ({version}) with incompatible format");
            return Ok(None);
        }

        // Unknown (newer) regulation versions cannot be parsed; bail out
        // before reading so `rest` keeps the bytes and a write round-trips.
        if !Regulation::ver_size_map().contains_key(&version) {
            eprintln!("Warning: Skipping regulation with unknown version {version}");
            return Ok(None);
        }

        let start_bits = reader.bits_read;
        match Regulation::from_reader_with_ctx(
            reader,
            (Endian::Little, RegulationIdentifier::Version(version)),
        ) {
            Ok(regulation) => Ok(Some(regulation)),
            Err(e) => {
                // Modded (randomizer, Kraken-compressed) regulation is skipped
                // instead of failing the whole save; this app only reads event
                // flags. The consumed bytes are dropped, so writing such a save
                // back would lose its regulation block.
                eprintln!("Warning: Skipping unparseable regulation data ({e:?})");
                let bytes_read = (reader.bits_read - start_bits).div_ceil(8);
                let remaining_bytes = declared.saturating_sub(bytes_read);
                if remaining_bytes > 0 {
                    let mut skip_buf = vec![0u8; remaining_bytes];
                    reader.read_bytes(remaining_bytes, &mut skip_buf)?;
                }
                Ok(None)
            }
        }
    }

    fn write_regulation<W: std::io::Write>(
        writer: &mut deku::writer::Writer<W>,
        regulation: &Option<Regulation>,
    ) -> Result<(), DekuError> {
        match regulation {
            Some(reg) => reg.to_writer(writer, (Endian::Little, RegulationIdentifier::Size(0)))?,
            None => {} // Skip writing if regulation is None
        }
        Ok(())
    }

    pub(crate) fn read<R: std::io::Read>(
        reader: &mut deku::reader::Reader<R>,
        endian: Endian,
        start: usize,
        size: usize,
        is_ps: bool,
    ) -> Result<Self, DekuError> {
        Ok(Self::from_reader_with_ctx(
            reader,
            (endian, start, size, is_ps),
        )?)
    }

    pub(crate) fn write<W: std::io::Write>(
        writer: &mut deku::writer::Writer<W>,
        endian: Endian,
        start: usize,
        size: usize,
        is_ps: bool,
        user_data_11: &Self,
    ) -> Result<(), DekuError> {
        if is_ps {
            user_data_11.to_writer(writer, (endian, start, size, is_ps))?;
            return Ok(());
        }

        let mut buffer = Vec::new();
        {
            let mut temp_writer = Writer::new(Cursor::new(&mut buffer));
            user_data_11.to_writer(&mut temp_writer, (endian, start, size, is_ps))?;
        }

        Util::update_checksum(&mut buffer);

        writer.write_bytes(&buffer)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const PAYLOAD_LEN: usize = 64;

    /// PC layout: checksum, magic, unk, version, size, payload.
    fn block(version: u32, declared_size: u32) -> Vec<u8> {
        let mut bytes = vec![0xAB; 0x10];
        bytes.extend_from_slice(b"BND4");
        bytes.extend_from_slice(&2u32.to_le_bytes());
        bytes.extend_from_slice(&version.to_le_bytes());
        bytes.extend_from_slice(&declared_size.to_le_bytes());
        bytes.extend((0..PAYLOAD_LEN).map(|i| i as u8));
        bytes
    }

    fn read_block(bytes: &[u8]) -> UserData11 {
        let mut cursor = Cursor::new(bytes);
        let mut reader = deku::reader::Reader::new(&mut cursor);
        UserData11::read(&mut reader, Endian::Little, 0, bytes.len(), false)
            .expect("block should parse")
    }

    fn write_block(user_data_11: &UserData11, len: usize) -> Vec<u8> {
        let mut out = Vec::new();
        {
            let mut writer = Writer::new(Cursor::new(&mut out));
            user_data_11
                .to_writer(&mut writer, (Endian::Little, 0, len, false))
                .expect("block should write");
        }
        out
    }

    #[test]
    fn garbage_header_size_is_bounded_by_the_block() {
        // Issue #11: a 1.17.x save declared 704_643_072 bytes here.
        let bytes = block(11_730_034, 704_643_072);
        let parsed = read_block(&bytes);
        assert!(parsed.regulation.is_none());
        assert_eq!(parsed.rest.len(), PAYLOAD_LEN);
        assert_eq!(write_block(&parsed, bytes.len()), bytes);
    }

    #[test]
    fn unknown_version_keeps_payload_for_round_trip() {
        let bytes = block(99_999_999, PAYLOAD_LEN as u32);
        let parsed = read_block(&bytes);
        assert!(parsed.regulation.is_none());
        assert_eq!(parsed.rest.len(), PAYLOAD_LEN);
        assert_eq!(write_block(&parsed, bytes.len()), bytes);
    }
}
