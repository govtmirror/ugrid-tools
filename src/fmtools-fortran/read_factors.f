
program read_factors
  use netcdf
  implicit None
    
  ! Source ESMF weights files.
  character(len=*), parameter :: PATH = "/home/benkoziol/l/data/nfie/example-weights-files/weights_14-UpperColorado.nc"
  ! Holds data to read in from file.
  real, dimension(:), allocatable :: factorList
  ! Holds factor indices in expected ESMF shape.
  integer, dimension(:, :), allocatable :: factorIndexList
  
  call ReadESMFWeightsFile(PATH, factorList, factorIndexList)
   
  print *, factorList(1:4)
   
  deallocate(factorList)
  deallocate(factorIndexList)
  
  print *, 'read_factors - SUCCESS'
    
contains
  subroutine ReadESMFWeightsFile(path, factorList, factorIndexList)
    ! Path to the ESMF weights netCDF file.
    character(len=*), intent(in) :: path
    ! Holds data to read in from file.
    real, dimension(:), allocatable, intent(inout) :: factorList
    ! Holds factor indices in expected ESMF shape.
    integer, dimension(:, :), allocatable, intent(inout) :: factorIndexList
    
    ! The netCDF ID for the file, data variable, dimension, and length of the
    ! dimension.
    integer :: ncid, varid, dimid, len_n_s
    
    ! ## Dimension and variable names for the ESMF format. #####################
    
    ! Variables to read in.
    character(len=*), parameter :: VFACTORINDEXLIST_DST = "row"
    character(len=*), parameter :: VFACTORINDEXLIST_SRC = "col"
    character(len=*), parameter :: VFACTORLIST = "S"
    ! Length dimension for target read variable.
    character(len=*), parameter :: DFACTOR = "n_s"
    
    ! ##########################################################################
    
    ! Open the files and update the file identifier variable "ncid".
    call check_nf90(nf90_open(path, NF90_NOWRITE, ncid))
    
    ! Get the dimension identifier.
    call check_nf90(nf90_inq_dimid(ncid, DFACTOR, dimid))
    ! Get the length/size of the dimension.
    call check_nf90(nf90_inquire_dimension(ncid, dimid, len=len_n_s))
    
    ! Allocate our factor arrays now that we know the size of the dimension.
    allocate(factorList(len_n_s))
    allocate(factorIndexList(2, len_n_s))
     
    ! ## Read in the variables. ################################################
    
    call check_nf90(nf90_inq_varid(ncid, VFACTORINDEXLIST_DST, varid))
    call check_nf90(nf90_get_var(ncid, varid, factorIndexList(2, :)))
     
    call check_nf90(nf90_inq_varid(ncid, VFACTORINDEXLIST_SRC, varid))
    call check_nf90(nf90_get_var(ncid, varid, factorIndexList(1, :)))
     
    call check_nf90(nf90_inq_varid(ncid, VFACTORLIST, varid))
    call check_nf90(nf90_get_var(ncid, varid, factorList))
    
    ! ##########################################################################
     
    ! Close the file, freeing all resources.
    call check_nf90(nf90_close(ncid))
  end subroutine ReadESMFWeightsFile

  subroutine check_nf90(status)
    integer, intent(in) :: status

    if (status /= nf90_noerr) then 
      print *, trim(nf90_strerror(status))
      stop "Stopped"
    end if
  end subroutine check_nf90  
    
end program read_factors

