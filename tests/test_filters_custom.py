from sucuri import Environment
from tests.test_engine import get_file

def test_custom_filters(tmp_path):
    env = Environment()
    
    # Registering a custom filter test
    @env.register_filter('exclaim')
    def exclaim_filter(val):
        return f"{val}!!!"
        
    env.register_filter('reverse', lambda x: str(x)[::-1])
    
    template_file = tmp_path / "test_filter.suc"
    template_file.write_text("h1 {title | exclaim | reverse}")
    
    html = env.template(str(template_file), {"title": "Hello"})
    
    assert "h1" in html
    assert "!!!olleH" in html  # "Hello" -> "Hello!!!" -> "!!!olleH"
    
def test_custom_filters_in_hash_loop(tmp_path):
    env = Environment()
    
    @env.register_filter('multiply')
    def mult_filter(val):
        return str(int(val) * 2)
        
    template_file = tmp_path / "test_loop.suc"
    template_file.write_text('''ul
    <for item in items>
    li #item | multiply
    <endfor>
''')
    html = env.template(str(template_file), {"items": [1, 2, 3]})
    assert "<li>2</li>" in html
    assert "<li>4</li>" in html
    assert "<li>6</li>" in html
