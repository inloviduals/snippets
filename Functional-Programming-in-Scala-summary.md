# Chapter 1: What is functional programming?

### The problem it solves
Traditional imperative programming relies heavily on **side effects** (mutating variables, modifying data structures in place, throwing exceptions, performing I/O). Side effects make code notoriously difficult to test, reuse, parallelize, and reason about. If a function's behavior depends on hidden global state or alters the outside world, you cannot easily isolate it or compose it with other functions. Chapter 1 solves this by establishing a radical premise: **we can write any program using only pure functions**, pushing all side effects to the outer edges of the application.

### Core ideas
1. **Pure Functions:** A function is pure if it only computes a result based on its inputs and has no observable side effects. 
2. **Referential Transparency (RT):** An expression is RT if it can be replaced by its evaluated value without changing the program's meaning. This is the bedrock of functional reasoning.
3. **The Substitution Model:** Because of RT, we can reason about functional programs like algebraic equations, substituting equals for equals without needing to mentally simulate global state changes.
4. **Separation of Concerns:** We separate the *description* of a computation (the pure core) from its *interpretation/execution* (the impure shell that handles I/O or effects).

### Key code pattern
**Before (Impure):** The function performs a side effect (charging a credit card) and is impossible to test without a real payment gateway.
```scala
def buyCoffee(cc: CreditCard): Coffee = {
  val cup = new Coffee()
  cc.charge(cup.price) // Side effect!
  cup
}
```
**After (Pure):** The function returns the *description* of the effect as a value, allowing for easy testing, batching, and reuse.
```scala
def buyCoffee(cc: CreditCard): (Coffee, Charge) = {
  val cup = new Coffee()
  (cup, Charge(cc, cup.price)) // Returns effect as a value
}
```

### Vocabulary introduced
* **Pure function:** Same input always yields same output; no side effects.
* **Side effect:** Anything a function does other than returning a result (e.g., I/O, mutation).
* **Referential Transparency (RT):** An expression can be replaced by its value without altering program behavior.
* **Substitution model:** A mode of reasoning where evaluation is just replacing terms with their equivalent values.

### Mental model shift
**"Instead of thinking of a program as a sequence of instructions that mutate the world, think of it as a web of pure functions that transform data, with side effects treated as ordinary values."**

### Common pitfalls
* **The "I/O Blocker":** Beginners often think FP makes it impossible to write useful programs that interact with the real world (files, databases, UI). The book shows that FP restricts *how* we write programs, not *what* we can express.
* **Confusing purity with immutability:** While FP heavily uses immutability, purity is specifically about the lack of side effects and the presence of RT.

### Try it
Look at a function in your current codebase that writes to a database. How could you refactor it so that the database write is returned as a "command" object rather than executed immediately?

### Takeaway
Functional programming is a discipline that takes the best practices of modular, testable code to their logical extreme. By eliminating side effects from the core logic, we gain unprecedented modularity and equational reasoning capabilities.

---

# Chapter 3: Functional data structures

### The problem it solves
If we cannot mutate variables or modify data structures in place, how do we represent data that changes over time? Naively copying entire data structures every time a change occurs would be disastrously slow and memory-intensive. This chapter solves the problem of representing changing data efficiently without mutation.

### Core ideas
1. **Immutable Data Structures:** Data structures are inherently persistent; "modifying" them actually creates a new structure while leaving the original intact.
2. **Algebraic Data Types (ADTs):** Defined using `sealed trait` and `case class`, ADTs allow us to model complex data by combining sums (OR) and products (AND) of types.
3. **Pattern Matching:** The primary mechanism for deconstructing ADTs and writing recursive functions over them in a type-safe way.
4. **Data Sharing:** The secret to FP performance. When we "modify" an immutable list (e.g., adding to the front), we don't copy the tail; we simply create a new head node that points to the existing tail.

### Key code pattern
Defining an immutable, persistent singly linked list and using pattern matching to fold over it.
```scala
sealed trait List[+A]
case object Nil extends List[Nothing]
case class Cons[+A](head: A, tail: List[A]) extends List[A]

def foldRight[A,B](as: List[A], z: B)(f: (A, B) => B): B = as match {
  case Nil => z
  case Cons(x, xs) => f(x, foldRight(xs, z)(f))
}
```

### Vocabulary introduced
* **ADT (Algebraic Data Type):** A composite type formed by summing (traits) and multiplying (case classes) other types.
* **Pattern matching:** A control-flow mechanism that structurally deconstructs ADTs to bind variables and execute logic.
* **Data sharing / Persistence:** Reusing unchanged parts of a data structure in memory when creating "new" versions of it.

### Mental model shift
**"Instead of thinking 'I need to update this array in place', think 'I need to construct a new structure that shares the unchanged memory of the old one.'"**

### Common pitfalls
* **The "Copying" Fear:** Beginners assume immutable data structures require massive memory duplication. In reality, operations like `tail` or `append` are $O(1)$ or $O(N)$ (where $N$ is only the modified path) due to data sharing.
* **Stack Overflows:** Using `foldRight` on large lists causes `StackOverflowError` because it's not tail-recursive. (This motivates `foldLeft` and lazy streams later).

### Try it
Implement `dropWhile[A](l: List[A], f: A => Boolean): List[A]`. Because of data sharing, this operation should run in $O(1)$ time if the first element doesn't match the predicate. How does it achieve this?

### Takeaway
Functional data structures are not slower; they are just structured differently. By leveraging ADTs, pattern matching, and aggressive data sharing, we can write highly efficient, thread-safe code without ever mutating memory.

---

# Chapter 4: Handling errors without exceptions

### The problem it solves
Exceptions break Referential Transparency. An expression like `throw new Exception("fail")` changes meaning depending on whether it's inside a `try/catch` block, destroying the substitution model. Furthermore, exceptions are not type-safe; a function signature `Int => Int` hides the fact that it might crash. This chapter solves error handling by treating failures as ordinary, type-safe values.

### Core ideas
1. **Errors as Values:** Instead of throwing exceptions, functions return types that explicitly represent the possibility of failure.
2. **The `Option` Data Type:** Used for functions that are partial (undefined for some inputs). It forces the caller to handle the "missing" case.
3. **The `Either` Data Type:** Used when we need to know *why* a failure occurred, carrying an error message or exception on the `Left`, and a success value on the `Right`.
4. **Lifting and Combinators:** We use higher-order functions like `map`, `flatMap`, and `map2` to chain computations that might fail, avoiding boilerplate `if/else` or `try/catch` blocks.

### Key code pattern
Using `map2` to combine two potentially failing computations without explicit error checking.
```scala
def map2[A,B,C](a: Option[A], b: Option[B])(f: (A, B) => C): Option[C] = 
  a flatMap (aa => b map (bb => f(aa, bb)))

// Usage: If either parsing step fails, the whole chain safely aborts to None
val optAge: Option[Int] = Try(ageStr.toInt)
val optTickets: Option[Int] = Try(ticketsStr.toInt)
val rate: Option[Double] = map2(optAge, optTickets)(insuranceRateQuote)
```

### Vocabulary introduced
* **Option:** A type that encapsulates an optional value (`Some` or `None`).
* **Either:** A disjoint union type, conventionally used for error handling (`Left` for errors, `Right` for success).
* **Partial vs. Total Function:** A partial function is undefined for some inputs; `Option` turns partial functions into total ones.
* **Lifting:** Converting a function `A => B` into a function `Option[A] => Option[B]`.

### Mental model shift
**"Instead of thinking 'I'll just throw an exception and catch it later', think 'I will encode the possibility of failure into the return type and use combinators to elegantly chain operations.'"**

### Common pitfalls
* **Using `.get` on Option:** This defeats the purpose of the type system and can throw runtime exceptions. Use `getOrElse`, `map`, or `flatMap` instead.
* **Expecting `Either` to accumulate errors:** The standard `Either` monad short-circuits on the first `Left`. If you want to collect *all* validation errors (like in a web form), you need a different data type (like `Validation`, introduced in Chapter 12).

### Try it
Implement `sequence[A](a: List[Option[A]]): Option[List[A]]`. It should combine a list of Options into a single Option containing a list. If any Option is `None`, the result should be `None`.

### Takeaway
By representing errors as values, we regain Referential Transparency and type safety. The compiler becomes our best friend, forcing us to handle edge cases explicitly while keeping the core business logic clean and composable.

---

# Chapter 5: Strictness and Laziness

### The problem it solves
Strict evaluation (evaluating all arguments before a function call) often leads to inefficiencies. For example, chaining `map` and `filter` on a strict `List` creates multiple intermediate collections and requires multiple passes over the data. This chapter solves the problem of efficiency and modularity by introducing **non-strictness (laziness)**, allowing us to separate the *description* of a computation from its *evaluation*.

### Core ideas
1. **Strict vs. Non-strict:** A strict function evaluates all its arguments; a non-strict function may choose not to evaluate some arguments (using **Thunks**).
2. **Streams (Lazy Lists):** Data structures that evaluate their elements only on demand. They allow for infinite sequences and single-pass fusion of operations.
3. **Separation of Description and Evaluation:** Laziness lets us build a "recipe" for a massive computation and only execute the exact portion needed to produce the final result.
4. **Corecursion:** Unlike recursion (which consumes data and must terminate), corecursion *produces* data and only needs to be "productive" (capable of generating the next element in finite time).

### Key code pattern
Defining a lazy `Stream` and using a non-strict `foldRight` to implement early termination (`exists`).
```scala
sealed trait Stream[+A]
case class Cons[+A](h: () => A, t: () => Stream[A]) extends Stream[A] // Thunks!

// Non-strict foldRight: 'b' is passed by name, allowing early termination
def foldRight[B](z: => B)(f: (A, => B) => B): B = this match {
  case Cons(h, t) => f(h(), t().foldRight(z)(f))
  case _ => z
}
def exists(p: A => Boolean): Boolean = foldRight(false)((a, b) => p(a) || b)
```

### Vocabulary introduced
* **Strictness:** A function is strict if it evaluates all its arguments.
* **Thunk:** An unevaluated expression, typically wrapped in a zero-argument function `() => A`.
* **Stream:** A lazy, potentially infinite linked list.
* **Corecursion:** Generating data step-by-step without requiring a base case to terminate.
* **Memoization:** Caching the result of a thunk so it's only computed once.

### Mental model shift
**"Instead of thinking 'I must compute this entire collection right now', think 'I will construct a lazy pipeline of transformations and let the data flow through one element at a time.'"**

### Common pitfalls
* **Memory Leaks:** Holding onto the head of a long `Stream` while traversing it prevents the garbage collector from reclaiming processed elements.
* **Forgetting to Memoize:** If you don't wrap thunks in `lazy val` inside smart constructors, accessing the head of a Stream multiple times will recompute the expensive thunk every time.

### Try it
Implement `takeWhile` using `foldRight`. Because `foldRight` on a Stream is non-strict in its second argument, your `takeWhile` should stop traversing the stream the moment the predicate fails.

### Takeaway
Laziness is not just an optimization trick; it is a profound design tool. It allows us to write highly modular, reusable components (like `map` and `filter`) that automatically fuse into single-pass, memory-efficient loops without sacrificing composability.

---

# Chapter 6: Purely functional state

### The problem it solves
How do we write programs that require state (like a Random Number Generator, or a game loop) without relying on mutable global variables or side effects? This chapter solves the problem of stateful programming by making state transitions explicit, turning stateful APIs into pure functions.

### Core ideas
1. **Explicit State Transitions:** Instead of a function mutating a hidden state, it takes the current state as input and returns a tuple containing the result and the *new* state: `S => (A, S)`.
2. **The `State` Data Type:** We encapsulate the `S => (A, S)` transition into a `State` type (or type alias like `Rand`), allowing us to treat state actions as first-class values.
3. **Combinators for State:** We write higher-order functions (`map`, `map2`, `flatMap`, `sequence`) to automatically thread the state from one action to the next, eliminating boilerplate.
4. **Purely Functional Imperative Programming:** By using `for`-comprehensions (which desugar to `flatMap`), we can write stateful code that *looks* and *reads* like imperative code, but remains 100% pure.

### Key code pattern
Threading state explicitly, then abstracting it away using `flatMap` and `for`-comprehensions.
```scala
// Explicit state threading (tedious)
def randomPair(rng: RNG): ((Int, Int), RNG) = {
  val (i1, rng2) = rng.nextInt
  val (i2, rng3) = rng2.nextInt
  ((i1, i2), rng3)
}

// Using combinators / for-comprehensions (elegant)
def randomPair: Rand[(Int, Int)] = for {
  i1 <- int
  i2 <- int
} yield (i1, i2)
```

### Vocabulary introduced
* **State Action / Transition:** A function `S => (A, S)` that reads a state, produces a value, and yields a new state.
* **Combinator:** A higher-order function used to combine state actions (e.g., `map2`, `flatMap`).
* **Referential Transparency in State:** Achieved by never mutating a shared state, but rather passing immutable state snapshots.

### Mental model shift
**"Instead of thinking 'I need to update this variable', think 'I need to define a function that takes the old state and returns a new state alongside my result.'"**

### Common pitfalls
* **Manual State Threading:** Beginners often manually pass the `RNG` (or state) through every function call, leading to messy, error-prone "arrow code." The lesson is to stop and write a `flatMap` combinator to handle the threading for you.
* **Confusing `State` with `IO`:** `State` is for *local*, deterministic state transitions (like an RNG). `IO` is for *external*, non-deterministic effects.

### Try it
Implement `flatMap[A,B](f: Rand[A])(g: A => Rand[B]): Rand[B]`. This is the key to unlocking the ability to chain state-dependent actions (like retrying an RNG draw if the number is out of bounds).

### Takeaway
State is not the enemy of functional programming; *hidden, mutable* state is. By making state transitions explicit and encapsulating them in monadic combinators, we get the readability of imperative programming with the mathematical guarantees of pure functions.

---

# Chapter 7: Purely functional parallelism

### The problem it solves
Traditional concurrency relies on shared mutable memory, threads, and locks. This leads to race conditions, deadlocks, and code that is nearly impossible to test or compose. This chapter solves the problem by designing a purely functional API for parallelism, completely separating the *description* of concurrent computations from their *execution*.

### Core ideas
1. **Algebraic Design:** We start by inventing an ideal API (`Par[A]`) based on simple use cases and laws, deferring the choice of representation (like `ExecutorService` or `Future`) until later.
2. **Separation of Description and Execution:** A `Par[A]` is just a pure description of a computation. It doesn't actually run until we pass it to an interpreter (like `run(es)`).
3. **Explicit Forking:** We introduce `fork` to explicitly mark which computations should be evaluated in a separate logical thread, giving the programmer fine-grained control over parallelism policies.
4. **Non-blocking Representations:** To avoid deadlocks in fixed-size thread pools, we eventually move from blocking `Future`s to non-blocking, callback-based representations (using Actors or continuations).

### Key code pattern
Defining the `Par` algebra and using it to express a parallel divide-and-conquer sum.
```scala
// The Algebra (Description)
def unit[A](a: => A): Par[A]
def map2[A,B,C](a: Par[A], b: Par[B])(f: (A,B) => C): Par[C]
def fork[A](a: => Par[A]): Par[A]

// The Usage
def sum(ints: IndexedSeq[Int]): Par[Int] =
  if (ints.size <= 1) Par.unit(ints.headOption getOrElse 0)
  else {
    val (l,r) = ints.splitAt(ints.length/2)
    Par.map2(Par.fork(sum(l)), Par.fork(sum(r)))(_ + _)
  }
```

### Vocabulary introduced
* **Par[A]:** A data type representing a parallel computation that yields an `A`.
* **Algebra:** A set of operations and laws that define how data types interact, independent of their implementation.
* **Explicit Forking:** The act of deliberately requesting a computation to run asynchronously.
* **Deadlock:** A situation where threads are waiting on each other indefinitely (often caused by naive blocking implementations of `fork`).

### Mental model shift
**"Instead of thinking 'How do I spawn a thread and manage a lock?', think 'How do I declare these computations as independent, and let the runtime scheduler handle the threads?'"**

### Common pitfalls
* **The Deadlock Bug:** Implementing `fork` by immediately submitting a blocking `Callable` to a thread pool. If the pool has 1 thread, the outer task blocks waiting for the inner task, which can never run. This teaches the vital lesson of *non-blocking* representations.
* **Confusing `Par` with `Future`:** `java.util.concurrent.Future` is an imperative, blocking handle. `Par` is a pure, composable description.

### Try it
Prove (or disprove) the law `fork(x) == x`. If you implement `fork` using a standard thread pool, can you find a scenario (like a fixed thread pool of size 1) where this law breaks and causes a deadlock?

### Takeaway
By treating parallel computations as pure values and designing an algebra around them, we eliminate the unpredictability of shared state. We gain the ability to write highly concurrent code that is modular, testable, and mathematically sound.