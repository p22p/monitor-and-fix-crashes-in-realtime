import ReactDOMServer from 'react-dom/server';

export default function(node) {
  return ReactDOMServer.renderToStaticMarkup(node);
}
