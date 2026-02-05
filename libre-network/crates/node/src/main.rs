use node::node::LibreNode;
use tokio::runtime::Runtime;

#[tokio::main]
async fn main() {
    let mut node = LibreNode::new().await;
    node.start().await;
}
