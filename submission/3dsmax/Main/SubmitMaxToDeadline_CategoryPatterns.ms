--Format: 
	--1st subarray: INCLUDE patterns,
	--2nd subarray: EXCLUDE patterns,
	--3rd element: Category to assign to
	--4th element: Priority to assign, -1 means no change
	
SMTD_CategoryPatterns = #(
    #(#("*SomePattern*"), #(), "1_HIGH_PRIORITY", 90), --this is just an example, remember to end with a comma
    --ADD YOUR CATEGORY PATTERNS HERE...
    #(#("VO*"), #(), "3_MODERATE_PRIORITY", 50)
)
