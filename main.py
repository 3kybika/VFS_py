import argparse
import time
from winfspy import  FileSystem,  enable_debug_log
from winfspy.plumbing.winstuff import filetime_now, security_descriptor_factory

from fsOperations.InMemoryFileSystemOperations import InMemoryFileSystemOperations

from defines import container_path

def main(mountpoint, label, debug):
    if debug:
        enable_debug_log()

    operations = InMemoryFileSystemOperations(label, container_path)
    fs = FileSystem(
        mountpoint,
        operations,
        sector_size=512,
        sectors_per_allocation_unit=1,
        volume_creation_time=filetime_now(),
        volume_serial_number=0,
        file_info_timeout=1000,
        case_sensitive_search=1,
        case_preserved_names=1,
        unicode_on_disk=1,
        persistent_acls=1,
        post_cleanup_when_modified_only=1,
        um_file_context_is_user_context2=1,
        file_system_name=mountpoint,
        prefix="",
        # security_timeout_valid=1,
        # security_timeout=10000,
    )
    try:
        print('Starting FS')
        fs.start()
        print('FS started, keep it running for 100s')
        time.sleep(100)

    finally:
        print('Stopping FS')
        fs.stop()
        print('FS stopped')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mountpoint")
    parser.add_argument("-d", dest="debug", action="store_true")
    args = parser.parse_args()
    main(args.mountpoint, 'touille', args.debug)