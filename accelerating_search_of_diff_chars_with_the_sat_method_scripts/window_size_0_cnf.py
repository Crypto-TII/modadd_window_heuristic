def window_size_0_cnf(x0, x1, x2):
 result = (
  f'{x0}   {x1}   -{x2} 0 \n' 
  f'{x0}   {x2}   -{x1} 0 \n' 
  f'{x1}   {x2}   -{x0} 0 \n' 
  f'-{x0}   -{x1}   -{x2} 0 \n'
 ) 
 return result
