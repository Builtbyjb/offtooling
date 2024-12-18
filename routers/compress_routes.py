from fastapi import APIRouter, Request, UploadFile, status, HTTPException
from fastapi.templating import Jinja2Templates
from utills.utills import (
    ValidateExtention,
    ValidateType,
    saveFile,
    changeDisplayFileName,
    ValidateSize
)
from libs.compress import CompressImage, CompressVideo
from logger import logger
from typing import Annotated
from fastapi import Depends
from database.database import get_session
from sqlmodel import Session


database = Annotated[Session, Depends(get_session)]

router = APIRouter(
    prefix="/compress",
    tags=["Compress"],
)

templates = Jinja2Templates(directory="templates")


@router.get("/", status_code=status.HTTP_200_OK)
def get_compress_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="compress.html",
    )


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def compress_file(file: UploadFile, db: database):
    is_valid_size = ValidateSize(file.size)
    is_valid_type, content_type = ValidateType(file.headers['content-type'])
    is_valid_ext, ext = ValidateExtention(file.filename)

    if is_valid_size:
        if is_valid_type and is_valid_ext:

            # Compress image files
            if content_type == "image" or content_type == "application":
                file_name, original_filename = await saveFile(file, db)
                message, new_file_name, new_file_size = CompressImage(
                    file_name, ext, db
                )

                if message == "Success":
                    return {
                        "message": message,
                        "fileDisplayName": original_filename,
                        "fileDownloadName": new_file_name,
                        "compressedFileSize": new_file_size,
                    }
                else:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=message
                    )

            # Compress video files
            elif content_type == "video":
                file_name, original_filename = await saveFile(file, db)
                message, new_file_name, new_file_size = CompressVideo(
                    file_name, db
                )

                display_name = changeDisplayFileName(original_filename, 'mp4')

                if message == "Success":
                    return {
                        "message": message,
                        "fileDisplayName": display_name,
                        "fileDownloadName": new_file_name,
                        "compressedFileSize": new_file_size,
                    }
                else:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=message
                    )
            else:
                logger.info("Uploadded file must be an image or a video")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file must be an image or a video"
                )
        else:
            logger.info("Not a valid file type")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not a valid file type"
            )
    else:
        logger.info("Invalid file size")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file size"
        )
