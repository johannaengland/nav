import io
import zipfile

from nav.web.utils import (
    generate_qr_code,
    generate_qr_codes_as_byte_strings,
    generate_qr_codes_as_zip_file,
)


def test_generate_qr_code_returns_byte_buffer():
    qr_code = generate_qr_code(url="www.example.com", caption="buick.lab.uninett.no")
    assert isinstance(qr_code, io.BytesIO)


def test_generate_qr_codes_as_byte_strings_returns_list_of_byte_strings():
    qr_codes = generate_qr_codes_as_byte_strings(
        {"buick.lab.uninett.no": "www.example.com"}
    )
    assert isinstance(qr_codes, list)
    assert isinstance(qr_codes[0], str)


def test_generate_qr_codes_as_zip_file_saves_zip_file_under_given_path(tmp_path):
    file_path = tmp_path / "qr_codes.zip"
    generate_qr_codes_as_zip_file(
        {"buick.lab.uninett.no": "www.example.com"}, file_path
    )

    assert zipfile.is_zipfile(file_path)
    file = zipfile.ZipFile(file_path, "r")
    assert "buick.lab.uninett.no.png" in file.namelist()
