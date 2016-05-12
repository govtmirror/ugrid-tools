subroutine add(arr)
    real, dimension(:), intent(inout) :: arr
    
    arr(:) = arr(:) + 10
    
end subroutine add

program aa
    implicit None
    
    real, dimension(2) :: arr
    
    arr = (/1., 2. /)

    call add(arr)
    
    print *, arr

end program aa
