! gfortran -ffree-form -o /tmp/apply apply.f && /tmp/apply

logical function assert_real_array_equal(n, actual, desired) result(res)
    implicit None
    real, intent(in), dimension(n) :: actual, desired
    
    integer                        :: ii, n

    res = .true.
    do ii=1,n
        if (actual(ii) /= desired(ii)) then
            res = .false.
            exit
        end if
    end do
    
end function assert_real_array_equal


subroutine apply_weights(n_src, n_dst, src, dst, row, col, S)
    implicit None
    integer, intent(in)                   :: n_dst, n_src
    integer, dimension(n_dst), intent(in) :: col, row
    real, dimension(n_dst), intent(in)    :: S
    real, dimension(n_src), intent(in)    :: src
    real, dimension(n_dst), intent(inout) :: dst
    
    integer                               :: ii, jj
    real                                  :: weighted
    
    ! For each dst element, compute its weighted value.
    do ii=1,n_dst
        ! Reset the weighting at the start of each element's calculation.
        weighted = 0.
        ! For each source element, find the associated weights and apply those
        ! weights to the source data.
        do jj=1,n_src
            ! Check the weights apply to the current element.
            if (row(jj) == ii) then
                ! This accumulates the weighted value.
                weighted = weighted + S(jj) * src(col(jj))
            end if
        end do
        ! Insert the weighted value into the dst array.
        dst(ii) = weighted
    end do
    
end subroutine apply_weights


program apply
    implicit None
    
    ! The desired result from the weight calculation.
    real, dimension(3) :: desired

    ! Number of elements in the dst field.
    integer, parameter :: n_dst = 3
    ! Number of elements in the source field.
    integer, parameter :: n_src = 5

    ! Source data that will be weighted.
    real, dimension(10) :: src
    ! Weighted data.
    real, dimension(n_dst) :: dst
    ! Indices of "col" and "S" used to link weights and source data.
    integer, dimension(n_src) :: row
    ! Indices of the source data used in weight application.
    integer, dimension(n_src) :: col
    ! Contains weights to apply to the source data to get a weighted dst
    ! value.
    real, dimension(n_src) :: S
    ! Iteration variables.
    integer :: ii, jj
    ! Holds weighted value for dst
    real :: weighted
    ! Result of the array test.
    logical :: test_result
    ! Test function.
    logical :: assert_real_array_equal

    desired = (/1., 2., 3.25 /)
    row = (/1, 1, 2, 3, 3 /)
    col = (/3, 3, 5, 7, 8 /)
    S = (/0.5, 0.5, 1.0, 0.75, 0.25 /)
    src = (/0., 0., 1., 0., 2., 0., 3., 4., 0., 0. /)

    call apply_weights(n_src, n_dst, src, dst, row, col, S)

    test_result = assert_real_array_equal(n_dst, dst, desired)
    if (test_result .eqv. .true.) then
        print *, "Test PASSED"
    else
        print *, "Test FAILED"
    end if
            
end program apply

