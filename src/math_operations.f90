! math_operations.f90
! Eine einfache Fortran-Bibliothek für arithmetische Operationen

module math_operations
  implicit none
  private

  ! Öffentliche Schnittstellen
  public :: add, subtract, multiply, divide

contains
  ! Addition zweier Zahlen
  function add(a, b) result(res)
    real, intent(in) :: a, b
    real :: res

    res = a + b
  end function add

  ! Subtraktion zweier Zahlen
  function subtract(a, b) result(res)
    real, intent(in) :: a, b
    real :: res

    res = a - b
  end function subtract

  ! Multiplikation zweier Zahlen
  function multiply(a, b) result(res)
    real, intent(in) :: a, b
    real :: res

    res = a * b
  end function multiply

  ! Division zweier Zahlen
  function divide(a, b) result(res)
    real, intent(in) :: a, b
    real :: res

    if (abs(b) < tiny(b)) then
      print *, "Warnung: Division durch Null oder sehr kleine Zahl"
      res = huge(res)
    else
      res = a / b
    end if
  end function divide

end module math_operations