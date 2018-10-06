+<a href="#"><img src="https://user-images.githubusercontent.com/16294901/37826760-892cd0de-2e73-11e8-8ea1-2afc390c2ac0.png" height="300" align="right"></a>
# This is a very important project.
# Sucuri
Simple and efficient template engine for Python projects inspired by [PugJS](https://pugjs.org)

## Instaling
Install and update using [pip](https://pip.pypa.io/en/stable/quickstart/):
> pip install sucuri

## Creating a Sucuri Template
- Example of code:
```
html
    body
        h1 Title
        a(href='#') This is my link
```
As can be seen in the code example above, the sucuri development requires tabulation standardization. We do not determine the number of spaces, but it is necessary to keep the same number of spaces on the left in the whole code, because this quantity will inform if a certain TAG of the HTML will be contained within another one or not. With this, in the example above we will have the following HTML code:
```
<html>
    <body>
        <h1>Title</h1>
        <a href="#">This is my link</a>
    </body>
</html>
```

## Using
To use sucuri, you need to import the sucuri package into your Python file, the example below is an application that uses the sucuri to render in the [Flask](http://flask.pocoo.org/):
```
from sucuri import rendering
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route("/")
def index():
    template = rendering.template('template.suc')
    return render_template_string(template)
```

As can be seen in the example above, the template in the example is loaded from a file named `template.suc` which is in the project's root directory, however it could be in any project directory, such as `templates/template.suc` if you include a folder to group the templates. At the first access to the archive, it will take care of storing it in memory, thus making access to information less costly and more efficient. 

### Text
In sucuri, texts are described in two ways. It can be written after the declaration of the tag such as:
```
h1 Title
```
Result:
```
<h1>Title</h1>
```
Or you can type in more than one line using the `|` on the lines that are not the same as the tag, see example:
```
h3 Hello!
    | Text
    | with
    | more than
    | one line
```
Result:
```
<h3>Hello!
    Text
    with
    more than
    one line
</h3>
```

### Attributes
Just as in HTML the attributes in the sucuri must be separated by space and unlike the PugJS must be in a row only and can not be separated by commas. They must necessarily be enclosed in parentheses. See examples of the use of attributes below:
```
a(href='google.com') Google
a(class='button' href='google.com') Google
div(class='div-class')
```
- Result:
```
<a href="google.com">Google</a>
<a class="button" href="google.com">Google</a>
<div class="div-class"></div>
```

### Rendering of data
We already know (seen in the text above) that we can only use the `template('template_name')` function with a simple `.suc` file, however it is possible to pass information through a JSON to the template and the sucuri will automatically render the data in the proper location, see the example below:
- Sucuri file:
```
html
    body
        h1 Hello {a}
            | Title
            | More
        a(href='#') This is my link
        h3 {b}
```
- Python example with data:
```
from flask import Flask, render_template_string
from sucuri import rendering

app = Flask(__name__)

@app.route("/")
def index():
    template = rendering.template('template_data.suc',{"a": 1, "b": "Hello!"})
    return render_template_string(template)
```
- Result:
```
<html>
    <body>
        <h1>Hello 1
        Title
        More
        </h1>
        <a href="#">This is my link</a>
        <h3>Hello!</h3>
    </body>
</html>
```

### Injecting template
Code reuse can be done through injected templates. This facility makes reuse of the code very efficient and enables the creation of code components. In the sucuri the identification of an injection occurs through an `include` at the beginning of the .suc file and its use is carried out using the `+` symbol before the name of the file that was imported. See the example below using this feature:
- Sucuri file (`template_include.suc`):
```
include inc/link
include inc/list

html
    body
        h1 Hello
            | Title
            | More
        +link
        h3 Oh Yeahh
        +list
```
- File inside the folder `inc` called `link.suc` (`inc/link.suc`):
```
a(href='#') {text}
```
- File inside the folder `inc` called `list.suc` (`inc/list.suc`):
```
ul
    li A
    li B
```
- Python example:
```
from flask import Flask, render_template_string
from sucuri import rendering

app = Flask(__name__)

@app.route("/")
def index():
    template = rendering.template('template_include.suc',{"text": "Hello! I'm here!"})
    return render_template_string(template)
```
- Result:
```
<html>
    <body>
        <h1>Hello
        Title
        More
        </h1>
        <a href="#">Hello! I'm here!</a>
        <h3>Oh Yeahh</h3>
        <ul>
            <li>A</li>
            <li>B</li>
        </ul>
    </body>
</html>
```

### Condition (if)

It is possible to use conditional statements within Sucuri. Conditions are using the same form as Python's. Hence, the main operators are ```==``` and ```!=```. See an example below:
- Main file
```
from flask import Flask, render_template_string
from sucuri import rendering

app = Flask(__name__)

@app.route("/")
def index():
    template = rendering.template('template_if.suc',{"x": 1, "y": 3})
    return render_template_string(template)
```
- Sucuri file (`template_if.suc`):
```
include inc/if

html
    body
        h1 Hello
            | Title
            | More
        +if
```

- File inside the folder `inc` called `if.suc` (`inc/if.suc`):
```
<if x != y>
h2 The condition is True
<endif>
```
- Result:
```
<html>
    <body>
        <h1>Hello
            Title
            More
        </h1>
        <h2> The condtition is True </h2>
    </body>
</html>
```

### Loop (for)
Sucuri has a loop in collections of objects, so it is necessary to use the object that has this characteristic as a parameter and to use the information in that collection. See the example below:
- Main file
```
from flask import Flask, render_template_string
from sucuri import rendering

app = Flask(__name__)

@app.route("/")
def index():
    template = rendering.template('template.suc',{"text": "Hello! I'm here!", "var":[1, 2, 3, 4]})
    return render_template_string(template)
```
- Sucuri file (`template_include.suc`):
```
include inc/link
include inc/list

html
    body
        h1 Hello
            | Title
            | More
        +link
        h1 Test
        +list
```
- File inside the folder `inc` called `link.suc` (`inc/link.suc`):
```
a(href='#') {text}
```
- File inside the folder `inc` called `list.suc` (`inc/list.suc`):
```
ul
    <for a in var>
    li Value #a
    h1 test
    ul
        <for w in var>
        li Another #w
        <endfor>
    <endfor>
```
- Result:
```
<html>
    <body>
        <h1>Hello
            Title
            More
        </h1>
        <a href="#">Hello! I'm here!</a>
        <h1>Test</h1>
        <ul>
            <li>Value 1</li>
            <h1>test</h1>
            <ul>
                <li>Another 1</li>
                <li>Another 2</li>
                <li>Another 3</li>
                <li>Another 4</li>
            </ul>
            <li>Value 2</li>
            <h1>test</h1>
            <ul>
                <li>Another 1</li>
                <li>Another 2</li>
                <li>Another 3</li>
                <li>Another 4</li>
            </ul>
            <li>Value 3</li>
            <h1>test</h1>
            <ul>
                <li>Another 1</li>
                <li>Another 2</li>
                <li>Another 3</li>
                <li>Another 4</li>
            </ul>
            <li>Value 4</li>
            <h1>test</h1>
            <ul>
                <li>Another 1</li>
                <li>Another 2</li>
                <li>Another 3</li>
                <li>Another 4</li>
            </ul>
        </ul>
    </body>
</html>
```

### Lists

It is possible to generate unordered bullet list (```<ul>```) and checkboxex with Sucuri. This requires that the Python list given as argument is only a one dimension list for unordered lists and two (the list of the items and the list of the checked items) for the checkboxes. See an example below:
- Main file
```
from flask import Flask, render_template_string
from sucuri import rendering

app = Flask(__name__)

@app.route("/")
def index():
    template = rendering.template('template_list.suc',{"items": [1, "two", 3, "Five"], "checked": [1, "Five"]})
    return render_template_string(template)
```
- Sucuri file (`template_list.suc`):
```

html
    body
        h1 Hello
        list(items)
        list(items checked)
```

- Result:
```
<html>
    <body>
        <h1>Hello</h1>
        <ul>
            <li> 1 </li>
            <li> two </li>
            <li> 3 </li>
            <li> Five </li>
        </ul>
        <input type="checkbox" id="ck-1" checked="checked">1
        <input type="checkbox" id="ck-two">two
        <input type="checkbox" id="ck-3">3
        <input type="checkbox" id="ck-Five" checked="checked">Five
    </body>
</html>
```


### Injecting Style (css) or Script (js)
To inject style or script into your html, the sucuri uses the style command that should come before the commands that will translate the html, in this case along with the import of the file however with the `style` tag for `css` and the `script` tag for `js` files.
- Sucuri file (`template.suc`):
```
include inc/link
include inc/list
style static/css/style
script static/js/script

html
    body
        h1 Hello
            | Title
            | More
        +link
        h1 Test
        +list
```

- Include List:
```
style static/css/list
ul
    <for a in var>
    li Value #a
    h1(class='h1-red') test
    ul
        <for w in var>
        li Another #w
        <endfor>
    <endfor>
```

- `style` static/css/style.css
```
h1 {
    color: blue;
}
```

- `style` static/css/list.css
```
.h1-red {
    color: red;
}
```

- `script` static/js/script.js
```
function example() {
    console.log('test');
}
```

- Result:
```
<html>
   <head></head>
   <body>
      <h1>Hello
         Title
         More
      </h1>
      <a href="#">Hello! I'm here!</a>
      <h1>Test</h1>
      <ul>
         <li>Value 1</li>
         <h1 class="h1-red">test</h1>
         <ul>
            <li>Another 1</li>
            <li>Another 2</li>
            <li>Another 3</li>
            <li>Another 4</li>
         </ul>
         <li>Value 2</li>
         <h1 class="h1-red">test</h1>
         <ul>
            <li>Another 1</li>
            <li>Another 2</li>
            <li>Another 3</li>
            <li>Another 4</li>
         </ul>
         <li>Value 3</li>
         <h1 class="h1-red">test</h1>
         <ul>
            <li>Another 1</li>
            <li>Another 2</li>
            <li>Another 3</li>
            <li>Another 4</li>
         </ul>
         <li>Value 4</li>
         <h1 class="h1-red">test</h1>
         <ul>
            <li>Another 1</li>
            <li>Another 2</li>
            <li>Another 3</li>
            <li>Another 4</li>
         </ul>
      </ul>
      <style>h1 {
         color: blue;
         }.h1-red {
         color: red;
         }
      </style>
      <script>function example() {
         console.log('test');
         }
      </script>
   </body>
</html>
```
