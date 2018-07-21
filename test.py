import unittest

from sucuri import Files
from sucuri import rendering

class TestFiles( unittest.TestCase ):

    def test_add_files( self ):
        files = Files()
        name = 'test/inc/link.suc'
        files.add( name )

        self.assertEqual( ["a(href='#') {text}"], files.get( name ) )

    def test_inject( self ):
        files = Files()
        param = {"text": "Hello!", "list": [1, 2, 3, 4]}

        name = 'test/includefile.suc'
        files.add( name )

        rendered = files.template( name, param )
        self.assertIn('<html>', rendered )
        self.assertIn('</html>', rendered )
        self.assertIn('<ul>', rendered )
        self.assertIn('</ul>', rendered )
        self.assertIn('<style>', rendered )
        self.assertIn('</style>', rendered )

        self.assertNotIn( 'test/inc/list', rendered )
        self.assertNotIn( '+link', rendered )
    
    def test_template( self ):
        files = Files()
        param = {"text": "Hello!", "list": [1, 2, 3, 4]}

        name = 'test/includefile.suc'
        files.add( name )

        rendered = files.template( name, param )

        self.assertEqual( rendered, rendering.template(name, param) )

if __name__ == '__main__':
    unittest.main()