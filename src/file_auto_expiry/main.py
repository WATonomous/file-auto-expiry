from .utils.interface import *
from .data.expiry_constants import SECS_PER_DAY
import time
import typer
app = typer.Typer()

@app.command()
def collect_file_info(path: str, save_file: str = "", days_for_expiry: int = 10, check_folder_atime: bool = False, overwrite_file: bool = True):
    """
    Collects information about the top level paths within a given folder path
    And dumps it into a json file, specified by the save_file flag
    """
    scrape_time = time.time()
    seconds_for_expiry = int(days_for_expiry) * SECS_PER_DAY
    expiry_threshold = scrape_time - seconds_for_expiry
    collect_expired_file_information(folder_path=path, 
                                     save_file=save_file, 
                                     scrape_time=scrape_time, 
                                     expiry_threshold=expiry_threshold,
                                     check_folder_atime=check_folder_atime,
                                     overwrite_file=overwrite_file)

@app.command()
def collect_creator_info(file_info: str, save_file_expiry: str = "",save_file_deletion: str = "", days_for_expiry: int = 10, overwrite_file: bool = True):
    """
    Tabulates the paths that relate to specific users, based on a given jsonl path
    That jsonl path should be the result of calling the collect_file_info function
    It then dumps the new information into another json file, specified by the save_file flag
    """
    scrape_time = time.time()
    collect_creator_information(days_for_expiry = days_for_expiry, 
                                path_info_file=file_info, 
                                save_file_expiry=save_file_expiry, 
                                save_file_deletion=save_file_deletion,
                                scrape_time=scrape_time,
                                overwrite_file=overwrite_file)

if __name__ == "__main__":
    app()