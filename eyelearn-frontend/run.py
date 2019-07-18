from app import create_app
import ssl

ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
ctx.load_cert_chain('ssl.crt', 'ssl.key')
if __name__ ==  "__main__":
    #app.run("0.0.0.0")
    app = create_app()
    app.run(debug=True)

    #app.run(host='0.0.0.0', ssl_context=ctx, threaded=True, debug=True)