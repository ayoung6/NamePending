# NamePending
A quick selfstudy into how language works

run the test file with `python2.7 NP.py test.np -r -a "Hello World!" 10 1`

## Hello World!
A hello world program is simple enough. Create a main lambda and call the print line function
```
main = lambda(arglist){
  println('Hello World!');
};
```
Alternatively, lambda can be replaced with `λ` for a shorthand lambda declaration
```
main = λ(arglist){
  println('Hello World!');
};
```

## Conditionals
NamePending uses the `if then else` style of if statement
```
if (conditional) then {
  If True
} else {
  If False
}; 
```

## Arrays/Lists
```
#declaration
list = [1, 2, 3, 4, 5];

#access
x = list[1]; #single value
y = list[0, 2, 4]; #sublist
```

## Loops
Loops are recursive
```
let loop(i = 0, limit = 10, step = 1){
  Do things here

  if (i < limit) then{
    i = i + step;
    loop(i, limit, step);
  }:
};
```

## Returns
NamePending uses cascading returns
Almost every code block can return a value. if statements, lets, functions
```
value = if (conditional) then{
  return 1;
} else {
  return 2;
};
```
```
func = lambda(){
  return 3;
};
value = func();
```
Cascading returns
```
value = let loop(i = 0){
  return if (i == 5) {
    return i;
  } else {
    loop(i + 1);
  };
};
```
