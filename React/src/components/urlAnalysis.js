import React from 'react'
import { Input, Tree, message, Spin, Icon } from 'antd'
import './themes/index'

const Search = Input.Search;
const TreeNode = Tree.TreeNode;


class UrlAnalysis extends React.Component{

    state = {
        keywords: [],
        taxonomy: {},
        spinDisplay: "none"
    }

    isUrl(url) {
        var strRegex ='(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]';
        var re = new RegExp(strRegex); 
        if(url !== "")
        {
            if (!re.test(url)) { 
                this.urlError();
                return false; 
            }
        }
        return true;
    }

    urlError = () => {
        message.error('Url is not correct');
    };

    onSearchUrl(url){
        // console.log(`search url:{url}`);

        if(url === ""){return;}
        if (this.isUrl(url)){
            this.setState({
                keywords: [],
                taxonomy: {}
            })
            this.request_analysis(url)
        }
    }

    handleAnalyseResult(result) {

        this.setState({
            keywords: result.keywords,
            taxonomy: result.taxonomy
        })
    }

    handleErrorCode(data){

        message.error('An unknown error has occurred.');
    }

    getTreeNodeData(nodeKey, nodeValue, nodePrefix, nodeIndex){

        let nodeData = {}
        let dataKey = nodePrefix + '-' + nodeIndex;

        if (nodeValue.length !== 0){

            let index = 0;
            let nodeChildren = []
            for (const key in nodeValue) {
                if (nodeValue.hasOwnProperty(key)) {
                    const element = nodeValue[key];
                    let child = this.getTreeNodeData(key, element, dataKey, index)
                    nodeChildren.push(child)
                }
                index++;
            }

            nodeData = {
                title: nodeKey,
                key: dataKey,
                children: nodeChildren
            }
        } else {
            nodeData = {
                title: nodeKey,
                key: dataKey
            }
        }
        return nodeData;
    }

    getTreeData(taxonomyData){

        let treeData = []
        
        let index = 0;
        for (const key in taxonomyData) {
            if (taxonomyData.hasOwnProperty(key)) {
                const element = taxonomyData[key];
                let nodeData = this.getTreeNodeData(key, element, '0', index);
                treeData.push(nodeData);
            }
            index++;
        }
        return treeData;
    }

    renderTreeNodes(data){
        return data.map((item) => {
            if (item.children) {
              return (
                <TreeNode title={item.title} key={item.key} dataRef={item}>
                  {this.renderTreeNodes(item.children)}
                </TreeNode>
              );
            }
            return <TreeNode {...item} />;
        });
    }

    request_analysis(url) {
        let data = {
            "url": url
        }
        let jsonStr = JSON.stringify(data);

        console.log(`request analyseUrl: {url}`);

        this.setState({
            spinDisplay: 'inline'
        })
        fetch('/analyseUrl', {
            method: "POST",
            headers: {"Content-Type": "application/json","charset": "utf-8"},
            body: jsonStr
        })
            .then(res => res.json())
            .then(data => {

                console.log(data);
                
                this.setState({
                    spinDisplay: 'none'
                })
                if (data.success === true) {
                    this.handleAnalyseResult(data.result)
                } else {
                    this.handleErrorCode(data)
                }
            })
            .catch((error) => {
                console.log(error);
                this.setState({
                    spinDisplay: 'none'
                })
            });
    }


    render() {

        //keywords
        let keyword_list = [];
        const array = this.state.keywords;
        for (let i = 0; i < array.length; i++) {
            const element = array[i];
            let size = 20 - 4 * (i/array.length);
            let font_size = size + 'px';
            let keyword = (<span key={i} style={{ fontSize: font_size, marginLeft: '12px' }}>{element}</span>);
            keyword_list.push(keyword);
        }

        //taxonomy
        let treeNodeList = []
        let that = this;
        for (const key in this.state.taxonomy) {
            let tree_key = 0;
            if (that.state.taxonomy.hasOwnProperty(key)) {
                const treeData = that.getTreeData(that.state.taxonomy[key]);
                const treeNodes = that.renderTreeNodes(treeData);
                treeNodeList.push(
                <Tree key={tree_key++} showLine>
                    {treeNodes}
                </Tree>)
            }
        }

        //spin
        const antIcon = <Icon type="loading" style={{ fontSize: 24, display: this.state.spinDisplay }} spin />;

        return(
            <div className='analysis-container'>
                <div className='analysis-header'>
                    <p className='analysis-title'>标签生成</p>
                </div>
                <div className='analysis-body'>
                    <Search 
                    className="analysis-search"
                    placeholder="输入网址"
                    enterButton="智能分析"
                    size="large"
                    onSearch={value => this.onSearchUrl(value)}
                    />

                    <div className='analysis-item'>
                        <label className='analysis-subtitle'>页面关键词</label>
                        <div className='keywords-container'>
                            {keyword_list}
                        </div>
                    </div>

                    <div className='analysis-item'>
                        <label className='analysis-subtitle'>标签树</label>
                        {treeNodeList}
                    </div>

                </div>

                <div className="analysis-spin">
                    <Spin indicator={antIcon} />
                </div>
            </div>
        );
    }
}

export default UrlAnalysis;