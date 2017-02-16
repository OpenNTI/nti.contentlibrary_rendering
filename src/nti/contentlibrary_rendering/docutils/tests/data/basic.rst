=============
Test RST File
=============

-------------
Inline Styles
-------------

basic text

++++++++
Emphasis
++++++++

This paragraph that will have **bold** and *italics* in it. We need to try nesting them like ** bold and *italic***, ***bold/italic***, and *italic and **bold*** (this format does not work).

Paragraph with an escaped \* in emphasis *Italics \* and a astrick*

Since the above format doesn't work and there is no support for underline, which while not necessarily that useful is expected by most users. We can use roles to also style text. Some roles like :emphasis:`emphasis`, :strong:`strong`, and :math:`math`; are built in. You can also define some custom roles, which we might need to do for all permutations of bold, italic, and underlined. For example :bolditalic:`bolditalic`, :boldunderlined:`boldunderline`, :italicunderlined:`italicunderlined`, :bolditalicunderlined:`bolditalicunderlined`.

-----
Lists
-----

+++++++++++++
Bulleted List
+++++++++++++

- Bullet List Item 1

    - Nested Bullet List Item 1-1
    - Nested Bullet List Item 1-2

        - Double Nested Bullet List Item 1-2-1
        - Double Nested Bullet List Item 1-2-2

    - Nested Bullet List Item 1-3
    - Nested Bullet List Item 1-4

- Bullet List Item 2

    - Nested Bullet List Item 2-1
    - Nested Bullet List Item 2-2
    - Nested Bullet List Item 2-3

- Bullet List Item 3
- Bullet List Item 4

+++++++++++++++
Enumerated List
+++++++++++++++

1. Ordered List Item 1

    (a) Nested Ordered List Item 1-1
    (b) Nested Ordered List Item 1-2

        i) Double Nested Ordered List Item 1-2-1
        ii) Double Nested Ordered List Item 1-2-2

    (c) Nested Ordered List Item 1-3
    (d) Nested Ordered List Item 1-4

2. Ordered List Item 2

    (a) Nested Ordered List Item 1-1
    (b) Nested Ordered List Item 1-2
    (c) Nested Ordered List Item 1-3

3. Ordered List Item 3
4. Ordered List Item 4
