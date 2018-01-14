import React, { Component } from 'react';

import {
    Col,
    Container,
    Row,
} from 'reactstrap';

import logo from './logo.svg';

import Header from './Header';
import DiscPanel from './DiscPanel';

import {
    subscribeToDriveInfo,
} from './api.js';

import './App.css';


class App extends Component {

    constructor(props) {
        super(props);
        this.state = {
            driveInfo: {},
        };
        subscribeToDriveInfo(this.handleDriveInfo);
    }

    handleDriveInfo(driveInfo) {
        let driveState = Object.assign({}, this.state.driveInfo);
        driveState[driveInfo.driveId] = driveInfo;
        this.setState({
            driveInfo: driveState,
        });
    }

    render(){
        return(
            <Container className="App" fluid>
                <Header />
                <Row>
                {
                    Object.keys(this.state.driveInfo).map((driveId) =>
                        <Col md="6" xs="12">
                            <DiscPanel driveId={driveId}
                                       discTitle={this.state.driveInfo[driveId].discTitle}
                                       />
                        </Col>
                    )
                }
                </Row>
            </Container>
        );
    }

}

export default App;
